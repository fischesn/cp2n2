"""Bounded macro-transition model compared with the actual control surface.

The model below does not call production admission, lifecycle or result checks.
Exploration is sequential; protocol transport and races have separate tests.
"""
from __future__ import annotations
from collections import deque
from dataclasses import asdict, dataclass, replace
from datetime import timedelta
from pathlib import Path
from threading import Thread
from unittest.mock import patch

from core.execution import PhaseOutcome, run_with_timeout
from evaluation.r3_enforcement import Environment
from evaluation.verify_r3_enforcement import effect_observations
from runtimes.biopattern_gate_sdk_runtime import write_json

ALPHABET = tuple(f"{verb}:{actor}" for verb in ("acquire", "prepare", "execute", "duplicate", "invalid_result", "timeout", "abort", "finish")
                 for actor in ("a", "b")) + ("expire", "reconcile")


@dataclass(frozen=True)
class State:
    owner: str | None = None
    lifecycle: str = "ready"
    slots: tuple[str, str] = ("none", "none")
    starts: int = 0
    commits: int = 0
    successes: int = 0


def transition(state, event):
    """Return expected state/acceptance, or None for an out-of-scope event."""
    verb, _, actor = event.partition(":")
    index = ("a", "b").index(actor) if actor else None
    slot = state.slots[index] if actor else None
    slots = list(state.slots)
    if verb == "acquire":
        accepted = state.owner is None and state.lifecycle == "ready"
        return (replace(state, owner=actor, lifecycle="reserved") if accepted else state), accepted
    if verb == "prepare":
        if slot != "none": return None
        accepted = state.owner == actor and state.lifecycle == "reserved"
        if accepted: slots[index] = "prepared"
        return replace(state, slots=tuple(slots)), accepted
    if verb in {"execute", "invalid_result", "timeout"}:
        if slot not in {"prepared", "stale"}: return None
        accepted = slot == "prepared" and state.owner == actor
        if not accepted: return state, False
        slots[index] = "succeeded" if verb == "execute" else "failed"
        return replace(state, owner=None, lifecycle="unreachable" if verb == "timeout" else "ready",
            slots=tuple(slots), starts=state.starts + 1, commits=state.commits + (verb != "timeout"),
            successes=state.successes + (verb == "execute")), True
    if verb == "duplicate":
        if slot not in {"succeeded", "failed", "aborted"}: return None
        return state, False
    if verb == "finish":
        if slot not in {"succeeded", "failed", "aborted"}: return None
        return state, True  # Read the already completed outcome, no execution.
    if verb == "abort":
        accepted = state.owner == actor
        if accepted and slot == "prepared": slots[index] = "aborted"
        return (replace(state, owner=None, lifecycle="ready", slots=tuple(slots)) if accepted else state), accepted
    if verb == "expire":
        if state.owner is None: return None
        slots = tuple("stale" if s == "prepared" else s for s in slots)
        return replace(state, owner=None, slots=slots), True
    if verb == "reconcile":
        accepted = state.owner is None
        return (replace(state, lifecycle="ready") if accepted else state), accepted
    raise ValueError(event)


class Driver:
    def __init__(self, directory):
        self.env = Environment(directory, protocol=False)
        self.reservations, self.prepared = {}, {}

    def apply(self, event):
        verb, _, actor = event.partition(":")
        env = self.env
        surface = env.owner if actor == "a" else env.other
        call = lambda tool, args: env.call(tool, args, surface=surface)
        if verb == "acquire":
            response = env.reserve(surface=surface)
            if response["ok"]: self.reservations[actor] = response
        elif verb == "prepare":
            reservation = self.reservations.get(actor, {"result": {"lease_id": "absent"}})["result"]
            response = call("prepare_assay", {"resource_id": env.resource_id, "preset_id": env.preset,
                "dry_run": False, "lease_id": reservation["lease_id"]})
            if response["ok"]: self.prepared[actor] = response
        elif verb in {"execute", "invalid_result", "timeout", "duplicate"}:
            prepared = self.prepared[actor]
            args = {"run_id": prepared["result"]["run_id"], "idempotency_key": f"slot-{actor}"}
            env.runtime.fault = "wrong_result_task" if verb == "invalid_result" else None
            if verb == "timeout":
                env.runtime.block, env.runtime.abort_confirmed = True, False
                env.runtime.started.clear()
                env.runtime.release.clear()
                env.records._records[args["run_id"]].task.invocation_timeout_ms = 23
                workers = []
                def logical_deadline(fn, timeout_ms):
                    if timeout_ms != 23: return run_with_timeout(fn, timeout_ms)
                    def owned_call():
                        try:
                            fn()
                        except RuntimeError:
                            if not env.runtime.cancelled:
                                raise
                    worker = Thread(target=owned_call, daemon=True)
                    workers.append(worker)
                    worker.start()
                    if not env.runtime.started.wait(2): raise RuntimeError("logical timeout did not start owned worker")
                    return PhaseOutcome(timed_out=True)
                try:
                    with patch("core.orchestrator.run_with_timeout", logical_deadline): response = call("run_assay", args)
                finally:
                    env.runtime.cancelled = True
                    env.runtime.release.set()
                    for worker in workers: worker.join(2)
                    if not env.runtime.done.wait(2): raise RuntimeError("logical timeout cleanup unresolved")
                    env.runtime.block, env.runtime.abort_confirmed = False, True
            else: response = call("run_assay", args)
        elif verb == "abort":
            prepared = self.prepared.get(actor)
            record = env.records.get(prepared["result"]["run_id"]) if prepared else None
            lease = env.orchestrator.registry.lease_store.current(env.resource_id)
            if record is not None and record.state == "prepared" and lease is not None and record.lease_id == lease.lease_id:
                response = call("abort_run", {"run_id": record.run_id})
            else:
                response = call("release_resource", {"resource_id": env.resource_id,
                    "lease_id": self.reservations.get(actor, {"result": {"lease_id": "absent"}})["result"]["lease_id"]})
        elif verb == "finish": response = call("get_run_status", {"run_id": self.prepared[actor]["result"]["run_id"]})
        elif verb == "expire":
            env.clock[0] += timedelta(seconds=61)
            env.orchestrator.registry.lease_store.current(env.resource_id)
            return True
        elif verb == "reconcile":
            return env.orchestrator.reconcile_backend(env.resource_id).success
        else: raise ValueError(event)
        return response["ok"]

    def observe(self):
        env = self.env
        observation = effect_observations(env.directory)
        lease = env.orchestrator.registry.lease_store.current(env.resource_id)
        successes = sum(r.state == "succeeded" for r in env.records._records.values())
        slots = []
        for actor in ("a", "b"):
            prepared = self.prepared.get(actor)
            if not prepared: slots.append("none")
            else:
                record = env.records.get(prepared["result"]["run_id"])
                slots.append("stale" if record.state == "prepared" and (lease is None or lease.lease_id != record.lease_id) else record.state)
        if observation["overlaps"] or observation["active"]: raise AssertionError("exclusive effects overlap or worker remains active")
        for record in env.records._records.values():
            if record.state == "succeeded":
                states = [t.to_state for t in record.result.lifecycle_history]
                if "validating" not in states: raise AssertionError("success lacks validation phase")
        return State(owner=lease.owner_id.removeprefix("owner-") if lease else None,
            lifecycle=env.orchestrator.registry.lifecycle_store.snapshot(env.resource_id).state,
            slots=tuple(slots), starts=len(observation["starts"]), commits=len(observation["commits"]), successes=successes)


def explore(directory, *, max_depth=6, prepared=False):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=prepared)
    if (root / "exploration.json").exists(): raise ValueError("exploration output already exists")
    queue, witnesses = deque([State()]), {State(): ()}
    rows, mismatches = [], []
    while queue:
        state = queue.popleft()
        witness = witnesses[state]
        if len(witness) >= max_depth: continue
        for event in ALPHABET:
            prediction = transition(state, event)
            if prediction is None: continue
            target, expected_acceptance = prediction
            trace = (*witness, event)
            driver = Driver(root / f"transition-{len(rows)+1:05d}")
            error = None
            observations = []
            try:
                expected = State()
                for step in trace:
                    expected, acceptance = transition(expected, step)
                    actual_acceptance = driver.apply(step)
                    actual = driver.observe()
                    observations.append({"event": step, "state": asdict(actual), "accepted": actual_acceptance})
                    if actual != expected or actual_acceptance != acceptance:
                        raise AssertionError(f"event {step}: expected {expected}/{acceptance}, observed {actual}/{actual_acceptance}")
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                mismatches.append({"trace": trace, "error": error})
            finally:
                write_json(driver.env.directory / "observations.json", {"trace": trace, "observations": observations})
                driver.env.cleanup()
                driver.env.save()
            rows.append({"trace": trace, "source": asdict(state), "target": asdict(target),
                "accepted": expected_acceptance, "matched": error is None, "error": error})
            if target not in witnesses:
                witnesses[target] = trace
                queue.append(target)
    report = {"schema_version": "r3-state-exploration-v1", "max_depth": max_depth, "alphabet": ALPHABET,
        "states": len(witnesses), "transitions": len(rows), "matched_transitions": sum(r["matched"] for r in rows),
        "verified": not mismatches, "mismatches": mismatches,
        "witnesses": [{"state": asdict(s), "trace": trace} for s, trace in witnesses.items()], "transitions_detail": rows}
    write_json(root / "exploration.json", report)
    return report
