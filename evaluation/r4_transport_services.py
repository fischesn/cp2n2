"""Isolated E1 effect provider and actual TCP stream fault proxy; no HTTP 503 injection."""
import argparse
import json
import os
from pathlib import Path
import socket
import socketserver
from threading import RLock
from time import perf_counter_ns,sleep
from datetime import datetime,timezone
from http.server import ThreadingHTTPServer

from adapters.edge_adapter import EdgeAdapter
from evaluation.r3_effect_backend import EffectAdapter
from remote.edge_service import EdgeServiceHandler,RemoteEdgeServiceState


class ProxyState:
    def __init__(self, target, rule, events):
        self.target=target; self.rule=Path(rule); self.events=Path(events)
        self.lock=RLock(); self.used=set()

    def log(self, **row):
        with self.lock:
            self.events.parent.mkdir(parents=True,exist_ok=True)
            with self.events.open("a",encoding="utf-8",newline="\n") as handle:
                handle.write(json.dumps({"at":datetime.now(timezone.utc).isoformat(),**row},sort_keys=True)+"\n")
                handle.flush(); os.fsync(handle.fileno())

    def decision(self, path):
        with self.lock:
            row=json.loads(self.rule.read_text(encoding="utf-8")) if self.rule.exists() else {}
            applicable=row.get("path") in (path,"*") and row.get("id") not in self.used
            if applicable and row.get("once",False): self.used.add(row["id"])
            return row if applicable else {}


class StreamProxy(socketserver.StreamRequestHandler):
    state: ProxyState

    def handle(self):
        self.request.settimeout(10)
        first=self.rfile.readline(65536)
        if not first: return
        path=first.decode("ascii").split(" ")[1]
        header=bytearray(first); length=0
        while True:
            line=self.rfile.readline(65536); header.extend(line)
            if line in (b"\r\n",b"\n",b""): break
            if line.lower().startswith(b"content-length:"): length=int(line.split(b":",1)[1])
        body=self.rfile.read(length)
        if path=="/health":
            content=b'{"status":"ok"}'
            self.request.sendall(b"HTTP/1.0 200 OK\r\nContent-Length: "+str(len(content)).encode()+b"\r\n\r\n"+content)
            return
        rule=self.state.decision(path)
        started=perf_counter_ns(); delay=rule.get("delay_ms",0)
        if delay: sleep(delay/1000)
        measured=(perf_counter_ns()-started)/1e6
        if rule.get("action")=="partition":
            self.state.log(path=path,action="partition",forwarded_bytes=0,withheld_response_bytes=0,
                requested_delay_ms=delay,measured_delay_ms=measured,closed_connection=True)
            return  # EOF without any fabricated HTTP response.
        forwarded=0; received=bytearray()
        try:
            with socket.create_connection(self.state.target,timeout=10) as upstream:
                raw=bytes(header)+body; upstream.sendall(raw); forwarded=len(raw)
                while chunk:=upstream.recv(65536): received.extend(chunk)
            dropped=rule.get("action")=="lost_reply"
            if not dropped: self.request.sendall(received)
            self.state.log(path=path,action="lost_reply" if dropped else "forward",
                forwarded_bytes=forwarded,received_response_bytes=len(received),
                withheld_response_bytes=len(received) if dropped else 0,
                requested_delay_ms=delay,measured_delay_ms=measured,closed_connection=dropped)
        except (OSError,TimeoutError) as exc:
            self.state.log(path=path,action="connection_error",forwarded_bytes=forwarded,
                received_response_bytes=len(received),withheld_response_bytes=0,
                requested_delay_ms=delay,measured_delay_ms=measured,
                closed_connection=True,error_type=type(exc).__name__)


class ProxyServer(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
    daemon_threads=True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("provider","proxy"),required=True)
    parser.add_argument("--host",default="127.0.0.1"); parser.add_argument("--port",type=int,required=True)
    parser.add_argument("--directory",type=Path); parser.add_argument("--target-port",type=int)
    parser.add_argument("--target-host",help="Upstream host; defaults to the bind host for the loopback fixture")
    parser.add_argument("--rule",type=Path); parser.add_argument("--events",type=Path)
    args=parser.parse_args()
    if args.mode=="provider":
        if args.directory is None: parser.error("provider requires --directory")
        state=RemoteEdgeServiceState()
        state.adapter=EffectAdapter(args.directory,wrapped=EdgeAdapter(backend_id="remote-edge-backend"))
        # Keep the historical remote descriptor used by the production binding.
        EdgeServiceHandler.state=state
        server=ThreadingHTTPServer((args.host,args.port),EdgeServiceHandler)
    else:
        if None in (args.target_port,args.rule,args.events): parser.error("proxy requires target port/rule/events")
        StreamProxy.state=ProxyState((args.target_host or args.host,args.target_port),args.rule,args.events)
        server=ProxyServer((args.host,args.port),StreamProxy)
    try: server.serve_forever()
    finally: server.server_close()


if __name__=="__main__": main()
