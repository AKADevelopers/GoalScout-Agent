from football_live_agent.models import Event, Match, Preferences
from football_live_agent.memory import FootballMemory
from football_live_agent.state import JsonState
from football_live_agent.watcher import run_once


class FakeProvider:
    def live_matches(self):
        return [
            Match("1", "Argentina", "Brazil", "World Cup", "LIVE", 44, 1, 0),
        ]

    def events_for_fixture(self, fixture_id):
        return [
            Event("1-goal-44-Argentina-Messi", "1", "goal", 44, "Argentina", "Messi", "Normal Goal"),
        ]


class CollectingNotifier:
    def __init__(self):
        self.messages = []

    def send(self, match, event):
        self.messages.append((match, event))


def test_run_once_sends_new_goal_once(tmp_path):
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina"],
        favorite_players=["Messi"],
        competitions=["World Cup"],
        alert_types=["goal"],
        timezone="Asia/Karachi",
    )
    notifier = CollectingNotifier()
    state = JsonState(tmp_path / "state.json")

    assert run_once(FakeProvider(), preferences, state, [notifier]) == 1
    assert run_once(FakeProvider(), preferences, state, [notifier]) == 0
    assert len(notifier.messages) == 1


def test_run_once_records_memory_for_last_match_and_event(tmp_path):
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina"],
        favorite_players=["Messi"],
        competitions=["World Cup"],
        alert_types=["goal"],
        timezone="Asia/Karachi",
    )
    notifier = CollectingNotifier()
    state = JsonState(tmp_path / "state.json")
    memory = FootballMemory(tmp_path / "memory.json")

    assert run_once(FakeProvider(), preferences, state, [notifier], memory=memory) == 1

    assert "Argentina 1-0 Brazil" in FootballMemory(tmp_path / "memory.json").summary()
