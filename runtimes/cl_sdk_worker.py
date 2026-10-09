"""Authorization-gated launcher for the unmodified official SDK entry point."""

from __future__ import annotations

import json
from pathlib import Path
import runpy
import sys
from time import monotonic, sleep


def main() -> None:
    app, config, output = sys.argv[1:]
    attempt_directory = Path(config).resolve().parent
    run_id = json.loads(Path(config).read_text(encoding="utf-8"))["run_id"]
    deadline = monotonic() + 10
    authorization = attempt_directory / "launch-authorized.json"
    while not authorization.exists():
        if monotonic() >= deadline:
            raise RuntimeError("SDK launch not authorized within ten seconds")
        sleep(0.02)
    binding = json.loads(authorization.read_text(encoding="utf-8"))
    if binding.get("sdk_run_id") != run_id or binding.get("contained") is not True:
        raise RuntimeError("SDK launch authorization mismatch")
    import cl
    if cl.is_simulator() is not True:
        raise RuntimeError("SDK worker is simulator-only")
    (attempt_directory / "sdk-started.json").write_text(
        json.dumps({"sdk_run_id": run_id, "runtime_kind": "sdk_simulator", "evidence_level": "E3"}) + "\n",
        encoding="utf-8",
    )
    sys.argv = ["cl.app.run", app, config, output]
    runpy.run_module("cl.app.run", run_name="__main__")


if __name__ == "__main__":
    main()
