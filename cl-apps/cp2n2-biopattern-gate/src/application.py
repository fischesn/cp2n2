"""Official CL application shell for the deterministic E3 campaign."""

from __future__ import annotations

import json
from pathlib import Path
from typing import override

import cl
from cl.app import BaseApplication, OutputType, RunSummary

from .biopattern_gate.config import BioPatternGateConfig
from .biopattern_gate.decoder import load_decoder
from .biopattern_gate.runner import run_session
from .biopattern_gate.simulator import DeterministicReservoirSimulator
from .config import BioPatternGateApplicationConfig


class BioPatternGateApplication(
    BaseApplication[BioPatternGateApplicationConfig]
):
    """E3-only shell; a distinct reviewed adapter will be required for CL1."""

    @override
    def run(
        self,
        config: BioPatternGateApplicationConfig,
        output_directory: str,
    ) -> RunSummary:
        if not cl.is_simulator():
            raise RuntimeError(
                "technical-e3 is simulator-only; no provider-approved CL1 preset exists"
            )
        package_root = Path(__file__).parent / "biopattern_gate"
        core_config = BioPatternGateConfig.model_validate_json(
            (
                package_root / "presets" / "simulator" / "technical-e3.json"
            ).read_text(encoding="utf-8")
        )
        decoder = load_decoder(
            package_root
            / "artifacts"
            / "simulator"
            / "pattern-gate-linear-v1.json"
        )
        if core_config.sha256() != config.config_sha256:
            raise RuntimeError("bundled configuration hash mismatch")
        if decoder.sha256() != config.decoder_sha256:
            raise RuntimeError("bundled decoder hash mismatch")

        result = run_session(
            run_id=config.run_id,
            config=core_config,
            decoder=decoder,
            port=DeterministicReservoirSimulator(),
        )
        summary = {
            **result.summary(),
            "substrate_executed": False,
            "pnn_evidence": False,
            "biological_claim": False,
            "attestation": "cl.is_simulator() == true",
        }
        output = Path(output_directory)
        output.mkdir(parents=True, exist_ok=True)
        (output / "result.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        content = (
            "# BioPattern Gate — E3 technical run\n\n"
            f"- Trials: {summary['trial_count']}\n"
            f"- Scored trials: {summary['scored_trial_count']}\n"
            f"- Sham trials: {summary['sham_trial_count']}\n"
            f"- Deterministic pipeline accuracy: {summary['accuracy']:.3f}\n"
            f"- Config: `{summary['config_sha256']}`\n"
            f"- Decoder: `{summary['decoder_sha256']}`\n\n"
            "**This simulator run is technical evidence only. It is not a "
            "biological PNN result.**\n"
        )
        (output / "summary.md").write_text(content, encoding="utf-8")
        return RunSummary(
            type=OutputType.MARKDOWN,
            content=content,
            runtime_kind="sdk_simulator",
            evidence_ceiling="E3",
            result=summary,
        )

    @staticmethod
    @override
    def config_class() -> type[BioPatternGateApplicationConfig]:
        return BioPatternGateApplicationConfig

