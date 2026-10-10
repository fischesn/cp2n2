"""Lightweight atomic JSON output for evaluation fixtures (no SDK import)."""
import json
from pathlib import Path
from uuid import uuid4


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_name(f"{path.name}.{uuid4()}.pending")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8", newline="\n")
    temporary.replace(path)
