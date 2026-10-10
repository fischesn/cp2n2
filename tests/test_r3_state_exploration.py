from evaluation.r3_state_exploration import State, explore, transition


def test_model_does_not_reuse_unknown_completion():
    s = State(owner="a", lifecycle="reserved", slots=("prepared", "none"))
    unknown, accepted = transition(s, "timeout:a")
    assert accepted and unknown.lifecycle == "unreachable" and unknown.starts == 1 and unknown.commits == 0
    assert transition(unknown, "acquire:b") == (unknown, False)
    restored, accepted = transition(unknown, "reconcile")
    assert accepted and restored.lifecycle == "ready"


def test_bounded_model_matches_control_surface(tmp_path):
    report = explore(tmp_path / "exploration", max_depth=4)
    assert report["verified"], report["mismatches"][:5]
    assert report["states"] > 20 and report["transitions"] > 50
