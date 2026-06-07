from football_live_agent.models import Event
from football_live_agent.state import JsonState


def test_seen_event_is_persisted(tmp_path):
    state = JsonState(tmp_path / "state.json")
    event = Event("fixture-goal-1", "fixture", "goal", 10, "Argentina", "Messi")

    assert state.mark_seen(event) is True
    assert state.mark_seen(event) is False

    reloaded = JsonState(tmp_path / "state.json")
    assert reloaded.mark_seen(event) is False
