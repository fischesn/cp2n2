"""Privacy transformations are narrow and publication verification fails closed."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("prepare_r5_zenodo", ROOT / "scripts/prepare_r5_zenodo.py")
packaging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packaging)
publish_spec = importlib.util.spec_from_file_location("publish_r5_zenodo", ROOT / "scripts/publish_r5_zenodo.py")
publisher = importlib.util.module_from_spec(publish_spec)
publish_spec.loader.exec_module(publisher)


class PublicPackagingTests(unittest.TestCase):
    def test_only_account_budget_removed(self):
        provider = {"requested_model": "example", "base_url": "https://example.org", "immutable_weights_verified": False,
                    "budget": {"spend": 0.1, "max_budget": 2.0, "reset_schedule": "weekly"}}
        result = json.loads(packaging.provider_public(json.dumps(provider).encode()))
        self.assertNotIn("budget", result)
        for key in ("requested_model", "base_url", "immutable_weights_verified"):
            self.assertEqual(result[key], provider[key])
        self.assertTrue(result["budget_metadata_redacted_for_publication"])

    def test_unexpected_budget_requires_review(self):
        with self.assertRaisesRegex(ValueError, "Unexpected provider"):
            packaging.provider_public(b'{"budget":{"unreviewed":1}}')

    def test_nested_financial_metadata_is_rejected(self):
        nested = packaging.zip_bytes({"provider.json": b'{"budget":{"spend":1}}'})
        with self.assertRaisesRegex(ValueError, "financial metadata remains"):
            packaging.audit_public({"probe.zip": nested}, [])

    def test_known_credential_is_rejected_without_echoing_it(self):
        secret = b"private-credential-value"
        with self.assertRaises(ValueError) as captured:
            packaging.audit_public({"data.bin": b"prefix:" + secret}, [secret])
        self.assertNotIn(secret.decode(), str(captured.exception))

    def test_hash_stable_zip_and_path_guard(self):
        self.assertEqual(packaging.zip_bytes({"data.txt": b"raw"}), packaging.zip_bytes({"data.txt": b"raw"}))
        with self.assertRaisesRegex(ValueError, "Unsafe archive member"):
            packaging.audit_public({"../outside.txt": b"unsafe"}, [])


class PublicationGuardTests(unittest.TestCase):
    def test_token_urls_and_foreign_hosts_rejected(self):
        for url in ("https://example.org/api/", "http://zenodo.org/api/",
                    "https://zenodo.org/api/?access_token=private", "https://user@zenodo.org/api/"):
            with self.assertRaises(ValueError):
                publisher.checked_url(url)

    def test_redirect_cannot_transmit_credential_to_foreign_host(self):
        class Session:
            calls = []

            def request(self, method, url, **kwargs):
                self.calls.append(url)
                return SimpleNamespace(status_code=301, headers={"Location": "https://example.org/api/"})

        session = Session()
        with self.assertRaises(ValueError):
            publisher.request(session, "GET", "https://zenodo.org/api/records/1")
        self.assertEqual(len(session.calls), 1)

    def test_post_redirect_is_not_replayed(self):
        class Session:
            calls = []

            def request(self, method, url, **kwargs):
                self.calls.append(url)
                return SimpleNamespace(status_code=302, headers={"Location": "/api/other"})

        session = Session()
        with self.assertRaisesRegex(RuntimeError, "HTTP 302"):
            publisher.request(session, "POST", "https://zenodo.org/api/deposit/depositions/1/actions/publish")
        self.assertEqual(len(session.calls), 1)

    def test_existing_creators_and_license_preserved(self):
        original = {"creators": [{"name": "Author, Example"}], "license": "mit-license"}
        result = publisher.metadata(original)
        self.assertEqual(result["creators"], original["creators"])
        self.assertEqual(result["license"], original["license"])
        self.assertEqual(result["version"], "R5-2026-10-10")

    def test_remote_checksum_mismatch_stops_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.txt"
            path.write_bytes(b"exact payload")
            deposit = {"files": [{"filename": path.name, "filesize": path.stat().st_size, "checksum": "0" * 32}]}
            with self.assertRaisesRegex(ValueError, "checksum/size differs"):
                publisher.verify_remote_files(deposit, [path])


if __name__ == "__main__":
    unittest.main()
