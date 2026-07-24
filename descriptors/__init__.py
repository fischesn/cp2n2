"""Descriptor and resource-contract models for the phys-MCP prototype."""

from descriptors.resource_contract import (
    CONTRACT_SCHEMA_VERSION,
    ContractAdmissionResult,
    PhysicalNeuralResourceContract,
    assess_contract_admission,
)

__all__ = [
    "CONTRACT_SCHEMA_VERSION",
    "ContractAdmissionResult",
    "PhysicalNeuralResourceContract",
    "assess_contract_admission",
]
