"""Offline guards for credential routing and supplementary deposit identity."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from publish_supplementary_zenodo import checked_url, inventory, metadata, verify_inherited


@pytest.mark.parametrize('url', [
    'http://zenodo.org/api/records/1',
    'https://example.org/api/records/1',
    'https://zenodo.org@evil.example/api/records/1',
    'https://zenodo.org/api/records/1?access_token=secret',
    'https://zenodo.org/api/records/1#fragment',
])
def test_credential_routing_is_host_and_scheme_pinned(url):
    with pytest.raises(ValueError):
        checked_url(url)


def test_allowed_api_url():
    url = 'https://zenodo.org/api/deposit/depositions/23281161'
    assert checked_url(url) == url


def test_inherited_records_cannot_be_silently_changed():
    original = {'files': [{'filename': 'baseline.zip', 'checksum': 'md5:abc', 'filesize': 12}]}
    expected = inventory(original)
    verify_inherited(original, expected)
    changed = {'files': [{'filename': 'baseline.zip', 'checksum': 'md5:def', 'filesize': 12}]}
    with pytest.raises(ValueError):
        verify_inherited(changed, expected)


def test_duplicate_remote_files_fail_closed():
    entry = {'filename': 'baseline.zip', 'checksum': 'abc', 'filesize': 12}
    with pytest.raises(ValueError):
        inventory({'files': [entry, entry]})


def test_metadata_preserves_creators_license_and_source_limits():
    original = {'license': 'mit-license', 'creators': [{'name': 'Fischer, Stefan'}]}
    result = metadata(original)
    assert result['creators'] == original['creators']
    assert result['license'] == original['license']
    assert result['version'] == 'SUPPLEMENTARY-2026-10-14'
    assert 'not 72 independent real workloads' in result['description']
    assert 'the base ' in result['description']
    assert 'Git commit does not identify them' in result['description']
    assert result['related_identifiers'][0]['identifier'] == '10.5281/zenodo.23281161'
