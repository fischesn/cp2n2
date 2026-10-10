"""Bounded separate-process loopback transport experiments; not container/network loss evidence."""
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns
from urllib.request import Request,urlopen
from urllib.parse import urlparse

from demos.common import make_edge_task
from evaluation.verify_r3_enforcement import effect_observations
from runtimes.biopattern_gate_sdk_runtime import write_json
from testbed.deployment import _free_port,_wait_until_ready,ManagedService

CONDITIONS=("baseline","delay","partition","lost_provider_reply","lost_client_reply",
            "provider_interrupt","controller_restart")
ROOT=Path(__file__).resolve().parents[1]


def request(url, task):
    began=perf_counter_ns()
    try:
        with urlopen(Request(url+"/execute",data=json.dumps({"task":task}).encode(),
            headers={"Content-Type":"application/json"},method="POST"),timeout=15) as response:
            result=json.loads(response.read())
        row={"delivered":True,"result":result}
    except (OSError,TimeoutError) as exc:
        row={"delivered":False,"error_type":type(exc).__name__}
    return {"task":task,"wall_ms":(perf_counter_ns()-began)/1e6,**row}


def trial(root, condition):
    if condition not in CONDITIONS: raise ValueError("unknown transport condition")
    root=Path(root); root.mkdir(parents=True,exist_ok=False)
    services=[]; process_rows=[]
    def start(name,module,arguments,port=None):
        selected_port=port or _free_port("127.0.0.1")
        logs=root/"logs"; logs.mkdir(exist_ok=True)
        handle=(logs/f"{name}.log").open("w",encoding="utf-8")
        try:
            process=subprocess.Popen([sys.executable,"-m",module,"--host","127.0.0.1","--port",str(selected_port),*arguments],
                cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,text=True,
                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        except BaseException:
            handle.close(); raise
        service=ManagedService(name,process,f"http://127.0.0.1:{selected_port}",handle)
        services.append(service)
        process_rows.append({"name":name,"pid":service.process.pid,"url":service.base_url,"module":module,"arguments":arguments})
        # Added before readiness probing so a startup failure cannot orphan it.
        _wait_until_ready(service)
        return service
    def port(service): return urlparse(service.base_url).port
    try:
        provider=start("provider","evaluation.r4_transport_services",
            ["--mode","provider","--directory",str(root/"provider/backend")])
        provider_rule=root/"provider-rule.json"; client_rule=root/"client-rule.json"
        write_json(provider_rule,{}); write_json(client_rule,{})
        provider_proxy=start("provider-proxy","evaluation.r4_transport_services",
            ["--mode","proxy","--target-port",str(port(provider)),"--rule",str(provider_rule),"--events",str(root/"provider-proxy.jsonl")])
        control_arguments=["--adapter-url",provider_proxy.base_url,"--profile",str(ROOT/"deployments/network-profiles/baseline-v1.json"),
            "--trace-path",str(root/"control-spans.jsonl")]
        control=start("control","remote.control_plane_service",control_arguments)
        client_proxy=start("client-proxy","evaluation.r4_transport_services",
            ["--mode","proxy","--target-port",str(port(control)),"--rule",str(client_rule),"--events",str(root/"client-proxy.jsonl")])
        if condition=="delay": write_json(provider_rule,{"id":"delay","path":"/invoke","delay_ms":50})
        elif condition=="partition": write_json(provider_rule,{"id":"partition","path":"*","action":"partition"})
        elif condition in ("lost_provider_reply","controller_restart"):
            write_json(provider_rule,{"id":"lost-provider","path":"/invoke","action":"lost_reply","once":True})
        elif condition=="lost_client_reply":
            write_json(client_rule,{"id":"lost-client","path":"/execute","action":"lost_reply","once":True})
        elif condition=="provider_interrupt": provider.stop()
        task=make_edge_task(task_id="r4-transport-task")
        task.direct_backend_id="remote-edge-backend"; task.allow_fallback=False
        task.client_id="r4-transport-client"; task.idempotency_key="r4-same-key"
        payload=task.model_dump(mode="json")
        first=request(client_proxy.base_url,payload)
        same=request(client_proxy.base_url,payload)
        new=None; restarted=None
        if condition in ("partition","lost_provider_reply","provider_interrupt","controller_restart"):
            new_payload={**payload,"task_id":"r4-new-task","idempotency_key":"r4-new-key"}
            new=request(client_proxy.base_url,new_payload)
        if condition=="controller_restart":
            old_port=port(control); control.stop()
            control=start("control-restarted","remote.control_plane_service",control_arguments,port=old_port)
            restarted=request(client_proxy.base_url,payload)
        write_json(root/"requests.json",{"condition":condition,"first":first,"same_key":same,"new_key":new,"after_restart":restarted})
    finally:
        for service in reversed(services): service.stop()
        write_json(root/"processes.json",{"processes":process_rows,"all_stopped":all(s.process.poll() is not None for s in services),
            "topology":"five Windows loopback processes including runner; no containers or second host"})
    return verify_trial(root)


def verify_trial(root):
    root=Path(root)
    data=json.loads((root/"requests.json").read_text(encoding="utf-8"))
    effects=effect_observations(root/"provider")
    condition=data["condition"]
    def succeeded(row): return bool(row and row["delivered"] and row["result"].get("success"))
    def replay(row): return bool(row["delivered"] and row["result"].get("idempotent_replay"))
    count=len(effects["commits"])
    expectation=True
    if condition in ("baseline","delay"):
        expectation=succeeded(data["first"]) and succeeded(data["same_key"]) and replay(data["same_key"]) and count==1
    elif condition=="lost_client_reply":
        expectation=not data["first"]["delivered"] and succeeded(data["same_key"]) and replay(data["same_key"]) and count==1
    elif condition in ("partition","provider_interrupt"):
        expectation=not succeeded(data["first"]) and not succeeded(data["same_key"]) and not succeeded(data["new_key"]) and count==0
    elif condition in ("lost_provider_reply","controller_restart"):
        expectation=not succeeded(data["first"]) and not succeeded(data["same_key"]) and replay(data["same_key"]) and not succeeded(data["new_key"])
        expectation=expectation and data["first"]["result"]["final_lifecycle"]["state"]=="unreachable"
        if condition=="controller_restart": expectation=expectation and succeeded(data["after_restart"]) and count==2
        else: expectation=expectation and count==1
    proxy_events=[]
    for name in ("provider-proxy.jsonl","client-proxy.jsonl"):
        if (root/name).exists(): proxy_events.extend(json.loads(line) for line in (root/name).read_text(encoding="utf-8").splitlines())
    delays=[r["measured_delay_ms"] for r in proxy_events if r.get("requested_delay_ms")==50]
    if condition=="delay": expectation=expectation and len(delays)==1 and delays[0]>=49
    if condition in ("lost_provider_reply","lost_client_reply","controller_restart"):
        lost=[e for e in proxy_events if e["action"]=="lost_reply"]
        expectation=expectation and len(lost)==1 and lost[0]["withheld_response_bytes"]>0 and lost[0]["forwarded_bytes"]>0
    if condition=="partition": expectation=expectation and any(e["action"]=="partition" and e["forwarded_bytes"]==0 for e in proxy_events)
    stopped=json.loads((root/"processes.json").read_text(encoding="utf-8"))["all_stopped"]
    return {"condition":condition,"expectation_matched":bool(expectation and stopped and not effects["active"] and not effects["overlaps"]),
        "starts":len(effects["starts"]),"commits":count,"overlaps":effects["overlaps"],
        "new_key_blocked":None if data["new_key"] is None else not succeeded(data["new_key"]),
        "restart_safety_supported":False if condition=="controller_restart" else None,
        "duplicate_after_restart_observed":condition=="controller_restart" and count>1,
        "first_final_lifecycle":data["first"].get("result",{}).get("final_lifecycle"),
        "first_error_code":data["first"].get("result",{}).get("error",{}).get("code") if data["first"].get("result",{}).get("error") else None,
        "measured_delay_ms":delays,"all_owned_processes_stopped":stopped,
        "scope":"actual TCP byte stream, separate processes, one host; not packets, containers or multi-host"}
