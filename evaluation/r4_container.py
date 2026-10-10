"""Isolated, source-frozen Docker extension of the bounded R4 TCP study."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from time import monotonic, perf_counter_ns, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4
import zipfile

from demos.common import make_edge_task
from evaluation.artifact_io import write_json
from evaluation.biopattern_gate_native import file_sha256
from evaluation.r3_archives import verify_files
from evaluation.r4_common import environment, finish
from evaluation.r4_transport import CONDITIONS
from evaluation.verify_r3_enforcement import effect_observations

ROOT = Path(__file__).resolve().parents[1]
OWNER_LABEL = "cp2n2.r4.owner"
PORT = 9000
ROLES = ("provider", "provider-proxy", "control", "client-proxy")
NEW_KEY_CONDITIONS = {"partition", "lost_provider_reply", "provider_interrupt", "controller_restart"}


def docker(*arguments, timeout=60, log=None):
    executable = shutil.which("docker")
    if not executable:
        raise RuntimeError("Docker CLI is not on PATH")
    result = subprocess.run([executable, *map(str, arguments)], capture_output=True,
                            encoding="utf-8", errors="replace", timeout=timeout,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if log is not None:
        Path(log).write_text(result.stdout + result.stderr, encoding="utf-8", newline="\n")
    if result.returncode:
        raise RuntimeError(f"docker {arguments[0]} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def inspect_container(identifier):
    return json.loads(docker("container", "inspect", identifier))[0]


def specification():
    task = make_edge_task(task_id="r4-container-task")
    task.direct_backend_id = "remote-edge-backend"
    task.allow_fallback = False
    task.client_id = "r4-container-client"
    task.idempotency_key = "r4-container-same-key"
    return {"schema": "r4-container-spec-v1", "conditions": list(CONDITIONS),
            "repetitions": 3, "delay_ms": 50, "execute_attempts": 57,
            "roles": list(ROLES), "task": task.model_dump(mode="json"),
            "containers": True, "multi_host": False, "packet_impairment": False,
            "transport": "HTTP over TCP; byte-stream proxies on a private Docker bridge",
            "durable_controller_state": False}


def snapshot_sources(path):
    files = set()
    folders = ("adapters", "agent", "applications", "cl-apps/cp2n2-biopattern-gate",
               "core", "descriptors", "evaluation", "mcp_surface", "runtimes", "scripts",
               "tests", "remote", "testbed", "twins", "demos", "deployments")
    for folder in folders:
        files.update(p for p in (ROOT / folder).rglob("*")
                     if p.is_file() and p.suffix in {".py", ".json"}
                     and not {"__pycache__", ".run-output"}.intersection(p.parts))
    files.update(ROOT / p for p in ("requirements.txt", "deployments/r4-container/Dockerfile",
                 "deployments/r4-container/requirements.txt", "docs/revision/r4-protocol.md",
                 "docs/revision/r4-container-protocol.md"))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(files):
            archive.writestr(item.relative_to(ROOT).as_posix(),
                             item.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n"))


def source_content_map(path):
    with zipfile.ZipFile(path) as archive:
        return {name: hashlib.sha256(archive.read(name)).hexdigest() for name in sorted(archive.namelist())}


def prepare(root):
    """Build and freeze inputs BEFORE any scored trial; never mount the checkout."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    spec = specification()
    write_json(root / "specification.json", spec)
    shutil.copyfile(ROOT / "docs/revision/r4-container-protocol.md", root / "protocol.md")
    host_environment = environment()
    host_environment["docker"] = json.loads(docker("version", "--format", "{{json .}}"))
    host_environment["docker_info"] = json.loads(docker("info", "--format",
        '{"os":{{json .OperatingSystem}},"kernel":{{json .KernelVersion}},"cpus":{{.NCPU}},"memory_bytes":{{.MemTotal}}}'))
    write_json(root / "environment.json", host_environment)
    snapshot_sources(root / "source-snapshot.zip")
    context = root / "build-context"
    source = context / "source"
    source.mkdir(parents=True)
    with zipfile.ZipFile(root / "source-snapshot.zip") as archive:
        for name in archive.namelist():
            if not (source / name).resolve().is_relative_to(source.resolve()):
                raise ValueError("source archive path escape")
        archive.extractall(source)
    shutil.copyfile(source / "deployments/r4-container/Dockerfile", context / "Dockerfile")
    shutil.copyfile(source / "deployments/r4-container/requirements.txt", context / "requirements.txt")
    base = json.loads(docker("image", "inspect", "python:3.12-slim"))[0]
    write_json(root / "base-image.json", base)
    base_ref = next((ref for ref in base.get("RepoDigests", []) if ref.startswith("python@")), None)
    if not base_ref:
        raise RuntimeError("The local Python base image has no immutable repository digest")
    tag = f"cp2n2-r4-container:{uuid4().hex}"
    docker("build", "--pull=false", "--progress=plain", "--tag", tag,
           "--build-arg", f"BASE_IMAGE={base_ref}", "--build-arg",
           f"SOURCE_SHA256={file_sha256(root / 'source-snapshot.zip')}", context,
           timeout=600, log=root / "image-build.log")
    image = json.loads(docker("image", "inspect", tag))[0]
    write_json(root / "image.json", image)
    image_id = image["Id"]
    docker("run", "--rm", "--network", "none", image_id, "python", "-c",
           "import evaluation.r4_transport_services; import remote.control_plane_service; print('service imports OK')",
           log=root / "image-import-check.log")
    source_probe = ("import hashlib,json; from pathlib import Path; p=Path('/app'); "
                    "print(json.dumps({f.relative_to(p).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() "
                    "for f in sorted(p.rglob('*')) if f.is_file()}))")
    actual_sources = json.loads(docker("run", "--rm", "--network", "none", image_id,
                                      "python", "-c", source_probe))
    if actual_sources != source_content_map(root / "source-snapshot.zip"):
        raise ValueError("built image source differs from frozen source ZIP")
    write_json(root / "image-source-content.json", actual_sources)
    runtime_probe = ("import json,platform,sys; from importlib.metadata import distributions; "
                     "print(json.dumps({'python':sys.version,'platform':platform.platform(),"
                     "'packages':{d.metadata['Name']:d.version for d in distributions()}}))")
    write_json(root / "container-environment.json", json.loads(docker("run", "--rm", "--network", "none",
               image_id, "python", "-c", runtime_probe)))
    report = docker("run", "--rm", "--network", "none", image_id,
                    "python", "-c", "from pathlib import Path; print(Path('/opt/r4-install-report.json').read_text())")
    write_json(root / "install-report.json", json.loads(report))
    docker("image", "save", "--output", root / "runtime-image.tar", image_id, timeout=300)
    names = ("specification.json", "protocol.md", "environment.json", "source-snapshot.zip",
             "base-image.json", "image.json", "image-source-content.json", "container-environment.json",
             "install-report.json", "runtime-image.tar")
    write_json(root / "freeze.json", {"schema": "r4-container-freeze-v1",
        "frozen_at": datetime.now(timezone.utc).isoformat(), "image_id": image_id,
        "inputs": {name: file_sha256(root / name) for name in names}})
    return root, spec, image_id


class DockerTrial:
    """Own only exact created IDs with a unique ownership label."""
    def __init__(self, root, image_id):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=False)
        self.image_id = image_id
        self.owner = uuid4().hex
        self.network_id = None
        self.containers = {}
        self.started = {}

    def network(self):
        self.network_id = docker("network", "create", "--driver", "bridge",
            "--label", f"{OWNER_LABEL}={self.owner}", f"cp2n2-r4-{self.owner[:12]}")
        write_json(self.root / "network.json", json.loads(docker("network", "inspect", self.network_id))[0])

    def create(self, role, module, arguments, *, publish=False):
        evidence = self.root / role
        evidence.mkdir()
        if "," in str(evidence):
            raise ValueError("Docker bind mount path contains a comma")
        command = ["create", "--name", f"cp2n2-r4-{self.owner[:12]}-{role}", "--init", "--log-driver", "json-file",
                   "--network", self.network_id, "--network-alias", role,
                   "--label", f"{OWNER_LABEL}={self.owner}", "--read-only", "--cap-drop", "ALL",
                   "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,size=16m",
                   "--mount", f"type=bind,source={evidence.resolve()},target=/evidence"]
        for variable in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
            command += ["--env", f"{variable}="]
        command += ["--env", "NO_PROXY=*", "--env", "no_proxy=*"]
        if publish:
            command += ["--publish", f"127.0.0.1::{PORT}"]
        command += [self.image_id, "python", "-m", module, "--host", "0.0.0.0",
                    "--port", str(PORT), *arguments]
        identifier = docker(*command)
        self.containers[role] = identifier  # Register before any start/readiness failure.
        docker("start", identifier)
        self.ready(role)
        self.started[role] = inspect_container(identifier)
        write_json(self.root / f"{role}-started.json", self.started[role])
        return identifier

    def ready(self, role):
        deadline = monotonic() + 30
        probe = f"from urllib.request import urlopen; assert urlopen('http://127.0.0.1:{PORT}/health',timeout=1).status == 200"
        while monotonic() < deadline:
            state = inspect_container(self.containers[role])["State"]
            if not state["Running"]:
                raise RuntimeError(f"{role} exited: {docker('logs', self.containers[role])}")
            try:
                docker("exec", self.containers[role], "python", "-c", probe, timeout=5)
                return
            except RuntimeError:
                sleep(.1)
        raise RuntimeError(f"{role} never became ready")

    def assert_owned(self, identifier):
        info = inspect_container(identifier)
        if info["Config"].get("Labels", {}).get(OWNER_LABEL) != self.owner:
            raise ValueError("refusing to mutate a container not owned by this trial")
        return info

    def stop(self, role):
        identifier = self.containers[role]
        self.assert_owned(identifier)
        docker("stop", "-t", "2", identifier, timeout=20)

    def restart(self, role):
        identifier = self.containers[role]
        self.assert_owned(identifier)
        docker("restart", "-t", "2", identifier, timeout=20)
        self.ready(role)
        write_json(self.root / f"{role}-restarted.json", inspect_container(identifier))

    def close(self):
        rows, errors = [], []
        for role, identifier in reversed(list(self.containers.items())):
            try:
                info = self.assert_owned(identifier)
                if info["State"]["Running"]:
                    docker("stop", "-t", "2", identifier, timeout=20)
                final = self.assert_owned(identifier)
                write_json(self.root / f"{role}-final.json", final)
                (self.root / f"{role}.log").write_text(docker("logs", "--timestamps", identifier), encoding="utf-8")
                docker("rm", identifier)  # No volume removal, prune, or name-pattern deletion.
                absent = identifier not in docker("ps", "--all", "--quiet", "--no-trunc").splitlines()
                rows.append({"role": role, "id": identifier, "removed": absent})
            except (RuntimeError, OSError, subprocess.SubprocessError, ValueError) as exc:
                errors.append({"role": role, "error": str(exc)})
        network_removed = self.network_id is None
        if self.network_id:
            try:
                info = json.loads(docker("network", "inspect", self.network_id))[0]
                if info.get("Labels", {}).get(OWNER_LABEL) != self.owner:
                    raise ValueError("refusing to remove an unowned Docker network")
                write_json(self.root / "network-final.json", info)
                docker("network", "rm", self.network_id)
                network_removed = self.network_id not in docker("network", "ls", "--quiet", "--no-trunc").splitlines()
            except (RuntimeError, OSError, subprocess.SubprocessError, ValueError) as exc:
                errors.append({"role": "network", "error": str(exc)})
        write_json(self.root / "cleanup.json", {"owner": self.owner, "containers": rows,
            "network_id": self.network_id, "network_removed": network_removed, "errors": errors,
            "complete": len(rows) == len(self.containers) and all(row["removed"] for row in rows) and network_removed and not errors})


def execute(url, task):
    began = perf_counter_ns()
    started_at = datetime.now(timezone.utc).isoformat()
    request = Request(url + "/execute", data=json.dumps({"task": task}).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=15) as response:
            row = {"delivered": True, "response_received": True, "http_status": response.status,
                   "result": json.loads(response.read())}
    except HTTPError as exc:
        row = {"delivered": False, "response_received": True, "http_status": exc.code,
               "http_error_body": json.loads(exc.read()), "error_type": type(exc).__name__}
    except (OSError, TimeoutError) as exc:
        row = {"delivered": False, "response_received": False, "http_status": None,
               "error_type": type(exc).__name__}
    return {"task": task, "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "wall_ms": (perf_counter_ns() - began) / 1e6, **row}


def trial(root, condition, image_id, spec):
    if condition not in spec["conditions"]:
        raise ValueError("unknown container condition")
    run = DockerTrial(root, image_id)
    try:
        run.network()
        run.create("provider", "evaluation.r4_transport_services",
                   ["--mode", "provider", "--directory", "/evidence/backend"])
        run.create("provider-proxy", "evaluation.r4_transport_services",
                   ["--mode", "proxy", "--target-host", "provider", "--target-port", str(PORT),
                    "--rule", "/evidence/rule.json", "--events", "/evidence/events.jsonl"])
        run.create("control", "remote.control_plane_service",
                   ["--adapter-url", f"http://provider-proxy:{PORT}",
                    "--profile", "/app/deployments/network-profiles/baseline-v1.json",
                    "--trace-path", "/evidence/spans.jsonl"])
        run.create("client-proxy", "evaluation.r4_transport_services",
                   ["--mode", "proxy", "--target-host", "control", "--target-port", str(PORT),
                    "--rule", "/evidence/rule.json", "--events", "/evidence/events.jsonl"], publish=True)
        root = run.root
        provider_rule, client_rule = {}, {}
        if condition == "delay":
            provider_rule = {"id": "delay", "path": "/invoke", "delay_ms": spec["delay_ms"]}
        elif condition == "partition":
            provider_rule = {"id": "partition", "path": "*", "action": "partition"}
        elif condition in ("lost_provider_reply", "controller_restart"):
            provider_rule = {"id": "lost-provider", "path": "/invoke", "action": "lost_reply", "once": True}
        elif condition == "lost_client_reply":
            client_rule = {"id": "lost-client", "path": "/execute", "action": "lost_reply", "once": True}
        write_json(root / "provider-proxy/rule.json", provider_rule)
        write_json(root / "client-proxy/rule.json", client_rule)
        if condition == "provider_interrupt":
            run.stop("provider")
        binding = run.started["client-proxy"]["NetworkSettings"]["Ports"][f"{PORT}/tcp"][0]
        if binding["HostIp"] != "127.0.0.1":
            raise ValueError("client port is not restricted to loopback")
        url = f"http://127.0.0.1:{binding['HostPort']}"
        payload = spec["task"]
        first, same = execute(url, payload), execute(url, payload)
        new = restarted = None
        if condition in NEW_KEY_CONDITIONS:
            new = execute(url, {**payload, "task_id": "r4-container-new-task", "idempotency_key": "r4-container-new-key"})
        if condition == "controller_restart":
            run.restart("control")
            restarted = execute(url, payload)
        write_json(root / "requests.json", {"condition": condition, "first": first,
            "same_key": same, "new_key": new, "after_restart": restarted})
    finally:
        run.close()
    return verify_trial(run.root, spec, image_id)


def verify_trial(root, spec, image_id):
    root = Path(root)
    read = lambda name: json.loads((root / name).read_text(encoding="utf-8"))
    data, cleanup = read("requests.json"), read("cleanup.json")
    condition = data["condition"]
    effects = effect_observations(root / "provider")
    succeeded = lambda row: bool(row and row["delivered"] and row["result"].get("success"))
    replay = lambda row: bool(row and row["delivered"] and row["result"].get("idempotent_replay"))
    first, same, new, restarted = (data[k] for k in ("first", "same_key", "new_key", "after_restart"))
    new_error = (new or {}).get("result", {}).get("error") or {}
    rows = [row for row in (first, same, new, restarted) if row is not None]
    if first["task"] != spec["task"] or same["task"] != spec["task"]:
        raise ValueError("within-trial original/same-key task differs from frozen input")
    expected_new = {**spec["task"], "task_id": "r4-container-new-task", "idempotency_key": "r4-container-new-key"}
    if (condition in NEW_KEY_CONDITIONS) != (new is not None) or (new and new["task"] != expected_new):
        raise ValueError("new-key coverage/task substitution")
    if (condition == "controller_restart") != (restarted is not None) or (restarted and restarted["task"] != spec["task"]):
        raise ValueError("restart coverage/task substitution")
    count = len(effects["commits"])
    effect_identity_ok = all(event["task_id"] == spec["task"]["task_id"]
        and event["principal_id"] == spec["task"]["client_id"]
        and event["request_key"] == spec["task"]["idempotency_key"]
        and event["backend_id"] == spec["task"]["direct_backend_id"]
        for event in [*effects["starts"], *effects["commits"]])
    if condition in ("baseline", "delay"):
        matched = succeeded(first) and succeeded(same) and replay(same) and count == 1
    elif condition == "lost_client_reply":
        matched = not first["response_received"] and succeeded(same) and replay(same) and count == 1
    elif condition in ("partition", "provider_interrupt"):
        matched = all(not succeeded(row) for row in rows) and count == 0
    elif condition in ("lost_provider_reply", "controller_restart"):
        matched = (not succeeded(first) and replay(same) and not succeeded(same) and
                   new["delivered"] and not succeeded(new) and new_error.get("code") == "POLICY_DENIED" and
                   (first.get("result", {}).get("final_lifecycle") or {}).get("state") == "unreachable")
        matched = matched and (count == 2 and succeeded(restarted) and not replay(restarted)
                              if condition == "controller_restart" else count == 1)
    else:
        raise ValueError("unknown condition in raw artifact")
    events = []
    for role in ("provider-proxy", "client-proxy"):
        path = root / role / "events.jsonl"
        events.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
    delays = [e["measured_delay_ms"] for e in events if e.get("requested_delay_ms") == spec["delay_ms"]]
    if condition == "delay":
        matched = matched and len(delays) == 1 and delays[0] >= spec["delay_ms"] - 1
    if condition in ("lost_provider_reply", "lost_client_reply", "controller_restart"):
        lost = [e for e in events if e["action"] == "lost_reply"]
        matched = matched and len(lost) == 1 and lost[0]["forwarded_bytes"] > 0 and lost[0]["withheld_response_bytes"] > 0 and lost[0]["closed_connection"]
    if condition == "partition":
        matched = matched and any(e["action"] == "partition" and e["forwarded_bytes"] == 0 and e["closed_connection"] for e in events)
    network = read("network.json")
    owner, network_id = cleanup["owner"], cleanup["network_id"]
    topology_ok = network["Id"] == network_id and not network["Internal"] and network["Driver"] == "bridge" and network["Labels"].get(OWNER_LABEL) == owner
    ids, ips, pids = set(), set(), set()
    for role in ROLES:
        started, final = read(f"{role}-started.json"), read(f"{role}-final.json")
        ids.add(started["Id"]); pids.add(started["State"]["Pid"])
        attached = list(started["NetworkSettings"]["Networks"].values())
        if len(attached) != 1:
            raise ValueError("container connected to an unexpected network")
        ips.add(attached[0]["IPAddress"])
        topology_ok = (topology_ok and started["Image"] == image_id and started["State"]["Running"]
            and started["Config"]["Labels"].get(OWNER_LABEL) == owner and final["Id"] == started["Id"]
            and not final["State"]["Running"] and attached[0]["NetworkID"] == network_id
            and started["HostConfig"]["ReadonlyRootfs"] and started["HostConfig"]["CapDrop"] == ["ALL"]
            and len(started["Mounts"]) == 1 and started["Mounts"][0]["Type"] == "bind"
            and started["Mounts"][0]["Destination"] == "/evidence")
        if role != "client-proxy":
            topology_ok = topology_ok and not started["HostConfig"]["PortBindings"]
    bindings = read("client-proxy-started.json")["NetworkSettings"]["Ports"][f"{PORT}/tcp"]
    topology_ok = topology_ok and len(bindings) == 1 and bindings[0]["HostIp"] == "127.0.0.1"
    topology_ok = topology_ok and len(ids) == len(ips) == len(pids) == 4 and "" not in ips and 0 not in pids
    final_network = read("network-final.json")
    cleanup_ok = (cleanup["complete"] and cleanup["network_removed"] and not cleanup["errors"]
                  and len(cleanup["containers"]) == 4 and {row["role"] for row in cleanup["containers"]} == set(ROLES)
                  and {row["id"] for row in cleanup["containers"]} == ids
                  and final_network["Id"] == network_id and not final_network["Containers"]
                  and final_network["Labels"].get(OWNER_LABEL) == owner
                  and all(row["removed"] for row in cleanup["containers"]))
    restart_ok = None
    if condition == "controller_restart":
        initial, after, final = read("control-started.json"), read("control-restarted.json"), read("control-final.json")
        provider_start, provider_final = read("provider-started.json"), read("provider-final.json")
        restart_ok = (after["Id"] == initial["Id"] == final["Id"] and after["State"]["Running"]
                      and after["State"]["StartedAt"] != initial["State"]["StartedAt"]
                      and after["State"]["Pid"] != initial["State"]["Pid"]
                      and provider_start["State"]["StartedAt"] == provider_final["State"]["StartedAt"])
        matched = matched and restart_ok
    return {"condition": condition, "expectation_matched": bool(matched and topology_ok and cleanup_ok and effect_identity_ok
                and not effects["active"] and not effects["overlaps"]),
            "starts": len(effects["starts"]), "commits": count, "overlaps": effects["overlaps"],
            "execute_attempts": len(rows), "http_500_responses": sum(row["http_status"] == 500 for row in rows),
            "measured_delay_ms": delays, "topology_verified": bool(topology_ok),
            "effect_identity_verified": effect_identity_ok,
            "new_key_error_code": new_error.get("code"),
            "all_owned_containers_and_network_removed": bool(cleanup_ok), "restart_verified": restart_ok,
            "duplicate_after_restart_observed": condition == "controller_restart" and count > 1,
            "durable_restart_safety_supported": False,
            "scope": "separate containers, one Docker Desktop VM/physical host; HTTP/TCP byte stream, not packets or MCP transport"}


def score(root, spec, image_id):
    expected = [(condition, i) for condition in spec["conditions"] for i in range(spec["repetitions"])]
    actual = json.loads((Path(root) / "trials.json").read_text(encoding="utf-8"))["trials"]
    if [(row["condition"], row["repetition"]) for row in actual] != expected:
        raise ValueError("container trial denominator/order substitution")
    reports, failures = [], []
    for row in actual:
        if row["directory"] != f"{row['condition']}/trial-{row['repetition']:02d}":
            raise ValueError("container trial directory substitution")
        path = Path(root) / row["directory"]
        if not path.resolve().is_relative_to(Path(root).resolve()):
            raise ValueError("trial directory escapes archive")
        if (path / "harness-failure.json").exists():
            failures.append(json.loads((path / "harness-failure.json").read_text(encoding="utf-8")))
        else:
            observed = verify_trial(path, spec, image_id)
            if observed["condition"] != row["condition"]:
                raise ValueError("raw trial condition differs from frozen trial order")
            reports.append(observed)
    attempts = sum(row["execute_attempts"] for row in reports)
    return {"kind": "container-transport", "verified": not failures and len(reports) == 21
                and attempts == spec["execute_attempts"] and all(row["expectation_matched"] for row in reports),
            "trials": reports, "harness_failures": failures, "planned_trials": 21,
            "execute_attempts": attempts, "expectation_matches": sum(row["expectation_matched"] for row in reports),
            "commits": sum(row["commits"] for row in reports),
            "http_500_responses": sum(row["http_500_responses"] for row in reports),
            "restart_duplicate_effect_trials": sum(row["duplicate_after_restart_observed"] for row in reports),
            "separate_container_extension_complete": not failures and all(row["topology_verified"] for row in reports) and len(reports) == 21,
            "multi_host": False, "packet_impairment": False, "durable_restart_safety_supported": False}


def run(root, spec, image_id):
    rows = []
    for condition in spec["conditions"]:
        for index in range(spec["repetitions"]):
            name = f"{condition}/trial-{index:02d}"
            path = root / name
            rows.append({"condition": condition, "repetition": index, "directory": name})
            try:
                result = trial(path, condition, image_id, spec)
                print(f"container {condition} {index+1}/3: effects={result['commits']}, expectation={result['expectation_matched']}", flush=True)
            except Exception as exc:
                path.mkdir(parents=True, exist_ok=True)
                write_json(path / "harness-failure.json", {"condition": condition, "repetition": index,
                    "error_type": type(exc).__name__, "error": str(exc)})
                print(f"container {condition} {index+1}/3: harness failure retained", flush=True)
    write_json(root / "trials.json", {"trials": rows})
    report = score(root, spec, image_id)
    finish(root, report)
    return report


def verify(root):
    root = Path(root).resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema"] != "r4-archive-v1":
        raise ValueError("unknown archive schema")
    verify_files(root, manifest["files"], excluded=("manifest.json",))
    frozen = json.loads((root / "freeze.json").read_text(encoding="utf-8"))
    if frozen["schema"] != "r4-container-freeze-v1":
        raise ValueError("unknown container freeze schema")
    expected_inputs = {"specification.json", "protocol.md", "environment.json", "source-snapshot.zip",
        "base-image.json", "image.json", "image-source-content.json", "container-environment.json",
        "install-report.json", "runtime-image.tar"}
    if set(frozen["inputs"]) != expected_inputs:
        raise ValueError("container frozen inventory changed")
    for name, digest in frozen["inputs"].items():
        if file_sha256(root / name) != digest:
            raise ValueError("container frozen input mismatch")
    spec = json.loads((root / "specification.json").read_text(encoding="utf-8"))
    if spec != specification():
        raise ValueError("container specification differs from protocol")
    image = json.loads((root / "image.json").read_text(encoding="utf-8"))
    if image["Id"] != frozen["image_id"] or image["Config"]["Labels"]["cp2n2.r4.source-sha256"] != frozen["inputs"]["source-snapshot.zip"]:
        raise ValueError("container image/source binding mismatch")
    contents = json.loads((root / "image-source-content.json").read_text(encoding="utf-8"))
    if contents != source_content_map(root / "source-snapshot.zip"):
        raise ValueError("image content differs from source snapshot")
    for condition in spec["conditions"]:
        for index in range(spec["repetitions"]):
            path = root / condition / f"trial-{index:02d}"
            if (path / "harness-failure.json").exists():
                continue
            data = json.loads((path / "requests.json").read_text(encoding="utf-8"))
            if data["first"]["started_at"] <= frozen["frozen_at"]:
                raise ValueError("confirmatory request predates the frozen inputs")
    report = score(root, spec, frozen["image_id"])
    if report != json.loads((root / "verification.json").read_text(encoding="utf-8")):
        raise ValueError("stored container report differs from offline recomputation")
    return report


def repair_packaging(root):
    """Repair ONLY the known nested-manifest omission, preserving its old inventory."""
    root = Path(root).resolve(strict=True)
    manifest_path = root / "manifest.json"
    previous = json.loads(manifest_path.read_text(encoding="utf-8"))
    frozen = json.loads((root / "freeze.json").read_text(encoding="utf-8"))
    if previous["schema"] != "r4-archive-v1" or frozen["schema"] != "r4-container-freeze-v1":
        raise ValueError("not a container archive with the known packaging schema")
    repair = root / "packaging-repair"
    if repair.exists():
        raise ValueError("packaging repair already recorded; do not replay it")
    for name, digest in {**previous["files"], **frozen["inputs"]}.items():
        path = (root / name).resolve(strict=True)
        if not path.is_relative_to(root) or file_sha256(path) != digest:
            raise ValueError("recorded measurement or frozen input changed before packaging repair")
    inventory = {p.relative_to(root).as_posix() for p in root.rglob("*")
                 if p.is_file() and p.relative_to(root).as_posix() != "manifest.json"}
    missing = inventory - set(previous["files"])
    if not missing or set(previous["files"]) - inventory:
        raise ValueError("not the known nested-manifest omission")
    contents = source_content_map(root / "source-snapshot.zip")
    for name in missing:
        prefix = "build-context/source/"
        original = name.removeprefix(prefix)
        if not name.startswith(prefix) or Path(name).name != "manifest.json" or original not in contents or file_sha256(root / name) != contents[original]:
            raise ValueError("omitted file is not an unchanged nested source manifest")
    spec = json.loads((root / "specification.json").read_text(encoding="utf-8"))
    report = score(root, spec, frozen["image_id"])
    stored = json.loads((root / "verification.json").read_text(encoding="utf-8"))
    if report != stored:
        raise ValueError("analysis differs; packaging-only repair refused")
    repair.mkdir()
    shutil.copyfile(manifest_path, repair / "manifest-before-repair.json")
    shutil.copyfile(ROOT / "evaluation/r4_common.py", repair / "r4_common.py")
    write_json(repair / "record.json", {"schema": "r4-container-packaging-repair-v1",
        "repaired_at": datetime.now(timezone.utc).isoformat(),
        "reason": "The shared exporter excluded every basename manifest.json instead of only the root manifest.",
        "omitted_unchanged_source_files": sorted(missing), "measurements_rerun": False,
        "frozen_inputs_changed": False, "analysis_changed": False,
        "verification_before_repair_sha256": file_sha256(root / "verification.json")})
    finish(root, report)
    return verify(root)
