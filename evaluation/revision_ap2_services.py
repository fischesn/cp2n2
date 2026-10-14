"""New AP2 fixture provider; production controller and runtime remain unchanged."""
import argparse
import json
from http.server import ThreadingHTTPServer
from pathlib import Path

from adapters.edge_adapter import EdgeAdapter
from evaluation.r3_effect_backend import EffectAdapter
from remote.edge_service import EdgeServiceHandler, RemoteEdgeServiceState


class ProviderHandler(EdgeServiceHandler):
    fault_path: Path

    def do_GET(self):
        if self.path == "/telemetry" and self.fault_path.exists():
            fault = json.loads(self.fault_path.read_text(encoding="utf-8"))
            if fault.get("invalid_frame"):
                self._send_json(200, ["invalid", "telemetry", "object"])
                return
        return super().do_GET()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--backend-id", required=True)
    parser.add_argument("--fault-path", type=Path, required=True)
    args = parser.parse_args()
    state = RemoteEdgeServiceState()
    state.adapter = EffectAdapter(args.directory, wrapped=EdgeAdapter(backend_id=args.backend_id))
    state.descriptor = state.adapter.describe().model_copy(deep=True)
    ProviderHandler.state = state
    ProviderHandler.fault_path = args.fault_path
    server = ThreadingHTTPServer((args.host, args.port), ProviderHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
