# Where-To-Watch Providers

GoalScout Agent only provides legal "where to watch" guidance. It must not provide pirate streams, illegal rebroadcasts, paywall bypasses, account sharing, or stream ripping steps.

## Categories

- **Live alerts**: Goals, cards, kickoff, fulltime, and match status.
- **Where to watch**: Official TV channels and streaming services showing a fixture.
- **My platforms**: The user's saved services, such as DAZN, ESPN+, Sky Sports, Peacock, Paramount+, Apple TV, Prime Video, Fubo, beIN Sports, FIFA+, Tapmad, or SonyLIV.
- **BYOK providers**: Official APIs that require the user to bring their own API key or partner token.

## Provider Support

### Built-in guide

Provider id: `guide`

No API key. Shows the user's saved country/platforms and explains the supported provider categories.

### Sportmonks TV Stations

Provider id: `sportmonks`

Environment variable:

```powershell
$env:SPORTMONKS_API_KEY = "<your-sportmonks-token>"
```

Fixture lookup:

```powershell
goalscout-agent where-to-watch <sportmonks-fixture-id> --provider sportmonks
```

Uses Sportmonks' TV station fixture endpoint:

```text
https://api.sportmonks.com/v3/football/tv-stations/fixtures/{ID}?api_token=YOUR_TOKEN
```

Returns broadcaster names, URLs when available, logos, and station type.

### TheSportsDB TV Broadcasts

Provider id: `thesportsdb`

Environment variable:

```powershell
$env:THESPORTSDB_API_KEY = "<your-thesportsdb-key>"
```

Fixture lookup:

```powershell
goalscout-agent where-to-watch <thesportsdb-event-id> --provider thesportsdb
```

Uses TheSportsDB event TV broadcast endpoint:

```text
https://www.thesportsdb.com/api/v1/json/{API_KEY}/lookuptv.php?id={EVENT_ID}
```

Returns TV channel names, country, and channel logo.

### Enterprise placeholders

These are documented BYOK categories. They require partner or enterprise access and should be configured only after the user has a valid contract:

- `sportradar`: `SPORTRADAR_API_KEY`
- `gracenote`: `GRACENOTE_API_KEY`
- `justwatch`: `JUSTWATCH_PARTNER_TOKEN`

If these are selected before integration credentials and route mapping exist, explain that they are official enterprise options and ask the user to confirm their provider account details.

## Famous Legal Platforms

Store these as user preferences, not as API keys:

- Global: DAZN, Prime Video, Apple TV, MLS Season Pass, FIFA+, YouTube.
- United States: ESPN, ESPN+, FOX Sports, Fubo, Peacock, NBC Sports, Paramount+, CBS Sports Golazo, Telemundo, Univision, ViX, YouTube TV, Sling, Hulu Live TV.
- UK/Ireland: Sky Sports, NOW, TNT Sports, discovery+, BBC iPlayer, ITV, Premier Sports.
- Europe/Middle East: beIN Sports, beIN SPORTS CONNECT, Canal+, Movistar Plus+, Viaplay, Ziggo Sport, Star+.
- South Asia: SonyLIV, JioCinema, FanCode, Tapmad, Tamasha, PTV Sports.

When official options match a user's saved platform, mention that clearly:

```text
- Peacock (United States) [you have this] - https://www.peacocktv.com
```
