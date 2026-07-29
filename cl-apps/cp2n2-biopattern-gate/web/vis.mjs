const dataStreams = [
  "pattern_gate/session",
  "pattern_gate/trial",
  "pattern_gate/gate",
  "pattern_gate/features",
  "pattern_gate/decision",
  "pattern_gate/control_status"
];

function createVisualiser(uniqueId, div) {
  const status = div.querySelector("#pattern-gate-status");
  status.textContent = "Technical E3 visualiser ready.";
  return {
    update(stream, data) {
      status.textContent = `${stream}: ${JSON.stringify(data)}`;
    }
  };
}
