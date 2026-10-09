# R1 comparison and citation decisions

**Date:** 9 October 2026. CP²N² contributes a PNN-specific operational contract
and reference integration, not a new lease, transport or distributed-consensus
algorithm. This comparison concerns documented responsibilities, not a measured
ranking of framework quality.

## Comparison criteria

Define the criteria before evaluating the approaches:

- **D Description:** identity, I/O units/encoding and declared operating bounds.
- **A Admission:** current-state feasibility, known/fresh observations and policy.
- **L Authority and lifecycle:** who may commit, ownership, state transitions,
  duplicate requests and uncertain-completion recovery.
- **V Result validity:** task/run identity, completeness, calibration context,
  independently checkable provenance and result postconditions.

Distinguish native mechanisms, a possible application extension, a demonstrated
integration and an out-of-scope obligation. A missing PNN example is not proof
that a framework cannot express the contract. In particular, no CP²N² integration
with MHS, PhysMCP, Kubernetes, ROS 2 or OPC UA is demonstrated here.

## Primary sources and integration boundary

| Approach and source version | Documented scope | CP²N² relationship |
|---|---|---|
| [MCP specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) | Discovery, schemas, invocation, protocol lifecycle and security responsibilities. | Retain transport/tool interaction; enforce domain obligations in the server/application. Not a replacement MCP protocol. |
| [PhysMCP specification v0.1](https://github.com/alexlqi/physmcp/blob/main/PhysMCP_v0.1.md) | Device-native tools/manifests, units/ranges/permissions, quality, feasibility and mesh recovery. | Acknowledge overlapping concerns. The domain binding is an assay-scoped PNN session, not a claim that device policy or recovery is absent. No PhysMCP conformance claim. |
| [MHS research preview, 27 August 2026](https://www.anthropic.com/news/model-hardware-standard-research-preview) | Agent-facing driver and device descriptions with operating limits and physical-device examples. | Possible future adapter integration. Announcement is not a complete conformance specification; do not score unannounced mechanisms as absent. |
| [W3C WoT Architecture 1.1](https://www.w3.org/TR/wot-architecture11/) | Thing descriptions/models and property/action/event interaction. | Provide PNN application/session policy and validity obligations above a possible WoT binding. |
| [Kubernetes Lease documentation](https://kubernetes.io/docs/concepts/architecture/leases/) | Coordination API used for heartbeats and leader election. | Leases/coordination are established mechanisms; an application must supply the PNN resource semantics. No Kubernetes-like HA guarantee for the in-memory prototype. |
| [ROS 2 managed-node lifecycle design](https://design.ros2.org/articles/node_lifecycle.html) | Managed states, transitions and supervisory responsibilities. | Reuse/relate to lifecycle concepts, with PNN-specific preparation, validation and uncertain-state handling. No general claim that ROS lacks lifecycle. |
| [OPC UA Part 1](https://reference.opcfoundation.org/specs/OPC-10000-1/full) and [Part 4](https://reference.opcfoundation.org/specs/OPC-10000-4), 1.05 series | Industrial information models and services. | Potential backend information/control binding; scientific calibration and assay postconditions still need domain definition. |
| NIR, mapping/compilers and CL/FinalSpark APIs, as cited in the manuscript | Model representation, substrate mapping or backend experiment operation. | Complementary backend-side layers; not evaluated as interchangeable PNN control planes. |
| CP²N² current prototype | PNRC admission, in-process ownership/lifecycle, structured results and E0--E3 software evidence. | Continuous MCP-to-official-SDK execution, complete semantic validators, restart/replication and physical validation remain outside existing results. |

The first four sources have explicit dated/versioned scopes. Kubernetes and
ROS pages are living documentation; the table does not claim a frozen software
release. OPC UA's reference site can redirect a versioned path to its current
index; keep the cited 1.05-series context explicit rather than treating the
redirect as a different tested implementation. PhysMCP's v0.1 file is on a
mutable branch; this check is not an immutable commit snapshot.

The revised paper replaces the binary all-yes/all-no feature table with
documented responsibility and remaining PNN binding. Its novelty statement
explicitly accounts for reused transport, state machines, leases, idempotency
and hash chains. No cross-framework performance or security comparison is made.

## Six references suggested by Reviewer 2

These are individual scope assessments. The published abstracts are sufficient
for the narrow inclusion decision below, not for claiming a full methodological
review. Suggested citations are not mandatory; each omission must receive a
courteous explanation in the final response.

| Suggested work | Primary source and access | Connection and decision |
|---|---|---|
| Requirements Are Not Specifications: A Socio-Technical Contract Perspective on Software Requirements | [DOI landing target](https://doi.org/10.1142/S0218194026500476); publisher text was unavailable in this check. Author institutional publication list confirms title/year, but no primary full-text assessment. | Potential conceptual connection to stakeholder requirements, not yet a verified basis for the executable PNRC contract. Do not add or assert detailed conclusions without publisher/author text. Reassess if coauthors provide it. |
| Comparative evaluation of natural language processing approaches with particle swarm optimized LightGBM for anomaly detection in cloud system logs | [Scientific Reports](https://doi.org/10.1038/s41598-026-51889-x), publisher abstract available. | Learned anomaly classification of logs is different from deterministic admission, identity-bound execution and fail-closed recovery. Omit from this focused control-contract comparison. |
| Applying metaheuristic optimization for insider-threat detection using natural language processing | [Springer publisher abstract](https://doi.org/10.1007/s41060-025-00996-5); full text subscription-limited. | Behavior/log classification and classifier optimisation do not establish authorization or PNN execution contracts. Omit; acknowledge it as a different security problem. |
| Tackling edge devices security by a two-level machine learning framework tuned by metaheuristics and enhanced with generative adversarial networks | [Machine Learning with Applications](https://doi.org/10.1016/j.mlwa.2026.100982), publisher abstract available. | Learned intrusion detection/data augmentation, not control-plane ownership, lifecycle or physical postconditions. Omit rather than imply CP²N² evaluates an IDS. |
| Intrusion detection in metaverse environment internet of things systems by metaheuristics tuned two level framework | [Scientific Reports](https://doi.org/10.1038/s41598-025-88135-9), publisher abstract available. | Attack classification for IoT networks is adjacent infrastructure security, not the tested admission/execution boundary. Omit from the focused comparison. |
| Enhancing Internet of Things Network Security Using Hybrid CNN and XGBoost Model Tuned via Modified Reptile Search Algorithm | [Applied Sciences](https://doi.org/10.3390/app132312687), publisher abstract available. | Network intrusion classifier/hyperparameter optimisation; no direct evidence for PNRC obligations. Omit with the same scoped rationale. |

No new intrusion-detection references are added merely to enlarge the
bibliography. This does not dispute their value for their own research questions.
The manuscript instead expands the directly related physical-interface and
general-middleware comparison. The unavailable requirements-contract paper is
an explicit source-access limit, not a negative assessment of its merits.
