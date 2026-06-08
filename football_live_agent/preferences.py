from __future__ import annotations

from dataclasses import replace

from football_live_agent.models import Preferences

SUPPORTED_DELIVERIES = {"console", "openclaw", "hermes", "webhook", "command"}
SUPPORTED_WATCH_PROVIDERS = {"guide", "sportmonks", "thesportsdb", "sportradar", "gracenote", "justwatch"}
SUPPORTED_ALERT_TYPES = {
    "goal",
    "penalty",
    "missed_penalty",
    "red_card",
    "yellow_card",
    "kickoff",
    "halftime",
    "fulltime",
    "substitution",
    "var_goal_cancelled",
    "var_penalty_confirmed",
    "all",
}
EMPTY_SENTINELS = {"none", "null", "n/a", "na"}

ALERT_ALIASES = {
    "missed penalty": "missed_penalty",
    "missed-penalty": "missed_penalty",
    "red card": "red_card",
    "yellow card": "yellow_card",
    "half time": "halftime",
    "full time": "fulltime",
    "sub": "substitution",
    "substitution": "substitution",
    "var goal cancelled": "var_goal_cancelled",
    "var penalty confirmed": "var_penalty_confirmed",
}


def normalize_alert_type(value: str) -> str:
    normalized = (value or "").strip().casefold().replace("_", " ")
    normalized = ALERT_ALIASES.get(normalized, normalized)
    return normalized.replace(" ", "_")


def validate_preferences(preferences: Preferences) -> list[str]:
    issues: list[str] = []
    delivery = _normalize(preferences.delivery)
    if delivery not in SUPPORTED_DELIVERIES:
        issues.append(f"Unsupported delivery mode: {preferences.delivery!r}.")

    if delivery in {"openclaw", "hermes"}:
        if not _normalize(preferences.channel):
            issues.append(f"{delivery} delivery needs a channel.")
        if not _normalize(preferences.target):
            issues.append(f"{delivery} delivery needs a target.")
    elif delivery == "webhook" and not _normalize(preferences.webhook_url):
        issues.append("webhook delivery needs a webhook URL.")
    elif delivery == "command" and not _normalize(preferences.channel_command):
        issues.append("command delivery needs a channel command template.")

    alerts = [_normalize_alert(alert) for alert in preferences.alert_types if _normalize_alert(alert)]
    if not alerts:
        issues.append("At least one alert type is required.")
    else:
        invalid_alerts = [alert for alert in alerts if alert not in SUPPORTED_ALERT_TYPES]
        if invalid_alerts:
            issues.append(f"Unsupported alert types: {', '.join(sorted(set(invalid_alerts)))}.")

    watch_provider = _normalize(preferences.watch_provider)
    if watch_provider and watch_provider not in SUPPORTED_WATCH_PROVIDERS:
        issues.append(f"Unsupported watch provider: {preferences.watch_provider!r}.")

    if not _normalize(preferences.timezone):
        issues.append("Timezone is required.")

    if preferences.quiet_hours_start and not preferences.quiet_hours_end:
        issues.append("Quiet hours end is required when quiet hours start is set.")
    if preferences.quiet_hours_end and not preferences.quiet_hours_start:
        issues.append("Quiet hours start is required when quiet hours end is set.")

    return issues


def repair_preferences(preferences: Preferences) -> tuple[Preferences, list[str]]:
    changes: list[str] = []
    original_delivery = (preferences.delivery or "").strip()
    delivery = _normalize(preferences.delivery) or "console"
    if delivery not in SUPPORTED_DELIVERIES:
        changes.append(f"delivery reset to console from {preferences.delivery!r}")
        delivery = "console"
    elif original_delivery != delivery:
        changes.append(f"delivery normalized to {delivery}")

    original_watch_provider = (preferences.watch_provider or "").strip()
    watch_provider = _normalize(preferences.watch_provider) or "guide"
    if watch_provider not in SUPPORTED_WATCH_PROVIDERS:
        changes.append(f"watch provider reset to guide from {preferences.watch_provider!r}")
        watch_provider = "guide"
    elif original_watch_provider != watch_provider:
        changes.append(f"watch provider normalized to {watch_provider}")

    original_alerts = [str(alert).strip() for alert in preferences.alert_types if str(alert).strip()]
    alert_types = []
    for alert in preferences.alert_types:
        normalized = normalize_alert_type(alert)
        if normalized and normalized not in alert_types:
            alert_types.append(normalized)
    if not alert_types:
        alert_types = ["goal", "red_card", "kickoff", "fulltime"]
        changes.append("alert types restored to the default set")
    else:
        invalid = [alert for alert in alert_types if alert not in SUPPORTED_ALERT_TYPES]
        if invalid:
            alert_types = [alert for alert in alert_types if alert in SUPPORTED_ALERT_TYPES]
            changes.append(f"removed unsupported alert types: {', '.join(sorted(set(invalid)))}")
    if alert_types != original_alerts:
        changes.append("alert types normalized")

    channel = _clean_text(preferences.channel)
    target = _clean_text(preferences.target)
    webhook_url = _clean_text(preferences.webhook_url)
    channel_command = _clean_text(preferences.channel_command)

    if delivery in {"openclaw", "hermes"} and (not channel or not target):
        changes.append(f"delivery reset to console because {delivery} needs both channel and target")
        delivery = "console"
    if delivery == "webhook" and not webhook_url:
        changes.append("delivery reset to console because webhook URL is missing")
        delivery = "console"
    if delivery == "command" and not channel_command:
        changes.append("delivery reset to console because channel command template is missing")
        delivery = "console"

    repaired = replace(
        preferences,
        favorite_country=_clean_text(preferences.favorite_country),
        favorite_teams=_clean_sequence(preferences.favorite_teams),
        favorite_players=_clean_sequence(preferences.favorite_players),
        competitions=_clean_sequence(preferences.competitions),
        alert_types=alert_types,
        timezone=_clean_text(preferences.timezone) or "UTC",
        quiet_hours_start=_clean_text(preferences.quiet_hours_start),
        quiet_hours_end=_clean_text(preferences.quiet_hours_end),
        webhook_url=webhook_url,
        delivery=delivery,
        channel=channel,
        target=target,
        channel_command=channel_command,
        watch_country=_clean_text(preferences.watch_country),
        watch_platforms=_clean_sequence(preferences.watch_platforms),
        watch_provider=watch_provider,
    )
    return repaired, changes


def _normalize(value: str | None) -> str:
    return (value or "").strip().casefold()


def _clean_text(value: str | None) -> str | None:
    text = (value or "").strip()
    if text.casefold() in EMPTY_SENTINELS:
        return None
    return text or None


def _clean_sequence(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        text = _clean_text(value)
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def _normalize_alert(value: str) -> str:
    return normalize_alert_type(value)
