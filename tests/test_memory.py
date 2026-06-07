from football_live_agent.memory import FootballMemory
from football_live_agent.models import Event, Match


def test_memory_records_last_match_event_and_notification(tmp_path):
    memory = FootballMemory(tmp_path / "memory.json")
    match = Match("1", "Argentina", "Brazil", "World Cup", "LIVE", 55, 2, 1)
    event = Event("1-goal-55", "1", "goal", 55, "Argentina", "Messi", "Normal Goal")

    memory.record_match(match)
    memory.record_event(match, event, notified=True)

    reloaded = FootballMemory(tmp_path / "memory.json")
    summary = reloaded.summary()

    assert "Argentina 2-1 Brazil" in summary
    assert "55'" in summary
    assert "GOAL" in summary
    assert "Messi" in summary


def test_memory_summary_handles_empty_file(tmp_path):
    memory = FootballMemory(tmp_path / "memory.json")

    assert memory.summary() == "No football memory yet."
