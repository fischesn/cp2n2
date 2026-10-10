import json
from pathlib import Path
from urllib.error import HTTPError
import io
import zipfile

import pytest

from evaluation import r4_container as campaign
from evaluation.artifact_io import write_json
from runtimes.biopattern_gate_sdk_runtime import write_json as sdk_write_json


def test_container_denominators_and_scope():
    spec = campaign.specification()
    assert len(spec["conditions"]) == 7 and spec["repetitions"] == 3
    attempts = sum(2 + (c in campaign.NEW_KEY_CONDITIONS) + (c == "controller_restart")
                   for c in spec["conditions"]) * spec["repetitions"]
    assert attempts == spec["execute_attempts"] == 57
    assert spec["containers"] and not spec["multi_host"] and not spec["packet_impairment"]
    assert not spec["durable_controller_state"]


def test_lightweight_json_writer_matches_sdk_serialization(tmp_path):
    data = {"b": [None, True, 1.2], "a": "result"}
    write_json(tmp_path / "light.json", data)
    sdk_write_json(tmp_path / "sdk.json", data)
    assert (tmp_path / "light.json").read_bytes() == (tmp_path / "sdk.json").read_bytes()
    assert not list(tmp_path.glob("*.pending"))


def test_container_snapshot_is_self_contained_and_excludes_local_secrets(tmp_path):
    path = tmp_path / "source.zip"
    campaign.snapshot_sources(path)
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
    assert {"remote/control_plane_service.py", "remote/edge_service.py", "twins/edge_twin.py",
            "testbed/config.py", "demos/common.py", "evaluation/artifact_io.py",
            "evaluation/r4_container.py", "deployments/r4-container/Dockerfile",
            "deployments/r4-container/requirements.txt", "docs/revision/r4-container-protocol.md"} <= names
    assert all(".env" not in Path(name).parts and "tmp" not in Path(name).parts
               and ".cp2n2" not in Path(name).parts for name in names)
    assert len(campaign.source_content_map(path)) == len(names)


def test_http_error_is_not_mistaken_for_no_response(monkeypatch):
    def failure(*args, **kwargs):
        raise HTTPError("http://test/execute", 500, "error", {}, io.BytesIO(b'{"error":"RemoteDisconnected"}'))
    monkeypatch.setattr(campaign, "urlopen", failure)
    row = campaign.execute("http://test", campaign.specification()["task"])
    assert not row["delivered"] and row["response_received"] and row["http_status"] == 500
    assert row["http_error_body"]["error"] == "RemoteDisconnected"


def test_connection_closure_has_no_http_status(monkeypatch):
    def failure(*args, **kwargs):
        raise ConnectionResetError("closed")
    monkeypatch.setattr(campaign, "urlopen", failure)
    row = campaign.execute("http://test", campaign.specification()["task"])
    assert not row["delivered"] and not row["response_received"] and row["http_status"] is None


def test_refuse_stop_of_unowned_container(tmp_path, monkeypatch):
    run = campaign.DockerTrial(tmp_path / "trial", "sha256:test")
    run.containers["provider"] = "other-id"
    monkeypatch.setattr(campaign, "inspect_container", lambda _: {"Config": {"Labels": {campaign.OWNER_LABEL: "someone-else"}}})
    commands = []
    monkeypatch.setattr(campaign, "docker", lambda *args, **kwargs: commands.append(args))
    with pytest.raises(ValueError, match="not owned"):
        run.stop("provider")
    assert commands == []


def test_create_registers_container_before_readiness_failure(tmp_path, monkeypatch):
    run = campaign.DockerTrial(tmp_path / "trial", "sha256:test")
    run.network_id = "own-network"
    commands = []
    def docker(*args, **kwargs):
        commands.append(args)
        return "new-container" if args[0] == "create" else ""
    monkeypatch.setattr(campaign, "docker", docker)
    def not_ready(role):
        raise RuntimeError("not ready")
    monkeypatch.setattr(run, "ready", not_ready)
    with pytest.raises(RuntimeError, match="not ready"):
        run.create("provider", "evaluation.r4_transport_services", ["--mode", "provider"])
    assert run.containers == {"provider": "new-container"}
    create = commands[0]
    assert "--read-only" in create and "--network" in create and "--privileged" not in create
    assert not any("docker.sock" in str(value) for value in create)
    assert "HTTP_PROXY=" in create and "NO_PROXY=*" in create


def test_cleanup_does_not_remove_foreign_resources(tmp_path, monkeypatch):
    run = campaign.DockerTrial(tmp_path / "trial", "sha256:test")
    run.containers["provider"] = "foreign-container"
    run.network_id = "foreign-network"
    monkeypatch.setattr(campaign, "inspect_container", lambda _: {"Config": {"Labels": {}}})
    commands = []
    def docker(*args, **kwargs):
        commands.append(args)
        if args[:2] == ("network", "inspect"):
            return json.dumps([{"Labels": {}}])
        raise AssertionError("no mutation should be called")
    monkeypatch.setattr(campaign, "docker", docker)
    run.close()
    cleanup = json.loads((run.root / "cleanup.json").read_text())
    assert not cleanup["complete"] and len(cleanup["errors"]) == 2
    assert commands == [("network", "inspect", "foreign-network")]


def test_trial_directory_substitution_is_rejected(tmp_path):
    spec = campaign.specification()
    rows = [{"condition": condition, "repetition": index, "directory": f"{condition}/trial-{index:02d}"}
            for condition in spec["conditions"] for index in range(spec["repetitions"])]
    rows[0]["directory"] = "other/trial-00"
    write_json(tmp_path / "trials.json", {"trials": rows})
    with pytest.raises(ValueError, match="directory substitution"):
        campaign.score(tmp_path, spec, "sha256:test")


def test_pre_run_hash_cannot_be_bypassed_by_repackaging(tmp_path):
    names = ("specification.json", "protocol.md", "environment.json", "source-snapshot.zip",
             "base-image.json", "image.json", "image-source-content.json", "container-environment.json",
             "install-report.json", "runtime-image.tar")
    for name in names:
        (tmp_path / name).write_bytes(b"{}")
    frozen = {"schema": "r4-container-freeze-v1", "image_id": "sha256:test",
              "inputs": {name: campaign.file_sha256(tmp_path / name) for name in names}}
    write_json(tmp_path / "freeze.json", frozen)
    # A later packaging manifest cannot redefine a pre-run frozen input.
    write_json(tmp_path / "environment.json", {"changed": True})
    campaign.finish(tmp_path, {})
    with pytest.raises(ValueError, match="frozen input mismatch"):
        campaign.verify(tmp_path)


def test_packaging_includes_nested_source_manifests(tmp_path):
    nested = tmp_path / "build-context/source/evaluation/results/example/manifest.json"
    nested.parent.mkdir(parents=True)
    write_json(nested, {"fixture": True})
    campaign.finish(tmp_path, {})
    inventory = json.loads((tmp_path / "manifest.json").read_text())["files"]
    assert nested.relative_to(tmp_path).as_posix() in inventory
    campaign.verify_files(tmp_path, inventory, excluded=("manifest.json",))
