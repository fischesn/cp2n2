"""Fabricated packaging fixtures only; no production/model/campaign execution."""
import io
import json
from pathlib import Path
import zipfile

import pytest

from scripts import prepare_supplementary_zenodo as package


@pytest.mark.parametrize("name", ["../secret", "/absolute", "a/../b", "a\\b", "C:/a",
    "a//b", "./a", ".env", "a/.env.local", "a/.git/config", "a/private.key"])
def test_unsafe_names_are_rejected(name):
    with pytest.raises(ValueError):
        package.safe_name(name)


def test_zip_deterministic_sorted_timestamp_and_exact_bytes():
    files = {"z.json": b'{"raw":1}\r\n', "a.txt": b"original\r\n"}
    first = package.deterministic_zip(files)
    assert first == package.deterministic_zip(dict(reversed(list(files.items()))))
    assert package.zip_members(first) == files
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert archive.namelist() == ["a.txt", "z.json"]
        assert all(info.date_time == package.DATE for info in archive.infolist())


@pytest.mark.parametrize("names", [("a", "a"), ("a", "A"), ("../bad",)])
def test_zip_rejects_duplicates_aliases_traversal(names):
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w") as archive:
        for name in names:
            archive.writestr(name, b"fabricated")
    with pytest.raises(ValueError):
        package.zip_members(target.getvalue())


@pytest.mark.parametrize("value", ["fabricated-secret", {"nested": "secret"}, ["secret"]])
def test_recursive_structured_credentials_rejected(value):
    files = {"a.json": json.dumps({"outer": [{"api_key": value}]}).encode()}
    with pytest.raises(ValueError, match="credential-valued"):
        package.scan_public_files(files)


def test_recursive_zip_and_jsonl_known_credential_check():
    inner = package.deterministic_zip({"a.jsonl": b'{"safe":"fabricated-private-value"}\n'})
    with pytest.raises(ValueError, match="known private credential"):
        package.scan_public_files({"source.zip": inner}, known=(b"fabricated-private-value",))


def test_budget_scan_counts_nested_fields_preserves_values_and_nan_fixture():
    raw = b'{"api_key":null,"cases":[{"max_cost":3,"nested":{"latency_budget_ms":10,"invalid":NaN}}]}\r\n'
    files = {"raw.json": raw}
    report = package.scan_public_files(files)
    assert report["budget_field_counts"] == {"max_cost": 1, "latency_budget_ms": 1}
    assert report["financial_values_redacted"] is False
    assert files["raw.json"] == raw


def test_duplicate_json_keys_fail_closed():
    with pytest.raises(ValueError, match="duplicate JSON"):
        package.scan_public_files({"a.json": b'{"api_key":null,"api_key":"secret"}'})


def _fake_archive():
    inputs = {"specification.json": b'{}\n', "source-snapshot.zip": package.deterministic_zip({"a.py": b"x=1\n"})}
    files = {**inputs, "outputs.json": b'{"passed":true}\n'}
    files["freeze.json"] = package.json_bytes({"inputs": {n: package.sha256(b) for n, b in inputs.items()}})
    files["manifest.json"] = package.json_bytes({"schema": "fabricated-v1", "files": {n: package.sha256(b) for n, b in files.items()}})
    return files


def test_frozen_input_and_output_hash_verification():
    files = _fake_archive()
    assert package.verify_campaign_bytes(files)["file_count"] == 5
    files["outputs.json"] += b" "
    with pytest.raises(ValueError, match="output hash"):
        package.verify_campaign_bytes(files)


def test_campaign_exact_inventory_required():
    files = _fake_archive()
    files["unexpected.json"] = b"{}"
    with pytest.raises(ValueError, match="inventory"):
        package.verify_campaign_bytes(files)


def test_source_binding_normalizes_newlines_not_other_bytes():
    files = {"source-snapshot.zip": package.deterministic_zip({"a.py": b"x=1\r\n"})}
    original = {"a.py": package.sha256(b"x=1\n")}
    assert package.source_binding(files, original)["original_unchanged_source_files"] == 1
    with pytest.raises(ValueError, match="identity"):
        package.source_binding(files, {"a.py": package.sha256(b"x=2\n")})


def test_extraction_fresh_directory_only_and_preserves_bytes(tmp_path):
    output = tmp_path / "fresh"
    files = {"a/raw.json": b"{}\r\n"}
    package.extract_files(files, output)
    assert (output / "a/raw.json").read_bytes() == files["a/raw.json"]
    with pytest.raises(FileExistsError):
        package.extract_files(files, output)


def test_public_verify_detects_tamper_before_extract_or_subprocess(tmp_path, monkeypatch):
    files = {"README.md": b"original"}
    files[package.MANIFEST_NAME] = package.json_bytes({"schema": "cp2n2-supplementary-public-package-v1", "files": {"README.md": package.sha256(b"not-original")}})
    path = tmp_path / "fake.zip"
    path.write_bytes(package.deterministic_zip(files))
    def forbidden(*args, **kwargs):
        raise AssertionError("No subprocess permitted in structural unit test")
    monkeypatch.setattr(package.subprocess, "run", forbidden)
    with pytest.raises(ValueError, match="package hash"):
        package.verify_public(path, tmp_path / "fresh")
    assert not (tmp_path / "fresh").exists()


def test_known_credentials_never_include_nonsecret_configuration(tmp_path):
    (tmp_path / ".env").write_text("ZENODO_ACCESS_TOKEN=fabricated-secret-value\nAI_LAB_BASE_URL=https://example.invalid\n", encoding="utf-8")
    values = package.known_credentials(tmp_path)
    assert b"fabricated-secret-value" in values
    assert not any(b"example.invalid" in value for value in values)
