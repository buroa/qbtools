# qbtools

## Description

qbtools is a feature rich CLI for the management of torrents in qBittorrent, written in Go 1.24 using the [github.com/autobrr/go-qbittorrent](https://github.com/autobrr/go-qbittorrent) client.

## Features

- **Tagging**: Automatically tag torrents based on tracker domains, status, duplicates, and age
- **CEL Expressions**: Use dynamic CEL (Common Expression Language) expressions for flexible torrent evaluation
- **Reannounce**: Automatically reannounce torrents with problematic trackers
- **Prune**: Remove torrents based on configurable tag criteria
- **Configurable**: Support for multiple tracker configurations with custom ratio and seeding requirements

## Table of contents

- [Description](#description)
- [Features](#features)
- [Table of contents](#table-of-contents)
- [Installation](#installation)
  - [Docker image](#docker-image)
  - [Building](#building)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Help](#help)
  - [Available Commands](#available-commands)
    - [Tagging](#tagging)
    - [Reannounce](#reannounce)
    - [Prune](#prune)

## Installation

### Docker image

Run a container with access to host network:

```bash
docker run -it --rm --network host ghcr.io/buroa/qbtools:latest tagging --unregistered
```

### Building

```bash
git clone https://github.com/buroa/qbtools.git && cd qbtools
docker build -t qbtools:latest --pull .
docker run -it --rm --network host qbtools --help
```

## Configuration

qbtools uses multiple configuration methods:

### Connection Settings

You can specify qBittorrent connection details using:

**Environment variables:**
- `QBITTORRENT_HOST`
- `QBITTORRENT_USERNAME`
- `QBITTORRENT_PASSWORD`

### Tracker Configuration

The `config.yaml` file contains tracker-specific settings including ratio requirements and seeding time limits. Each tracker entry includes:

- `name`: Short name for the tracker
- `required_seed_ratio`: Minimum ratio requirement
- `required_seed_days`: Minimum seeding time in days
- `urls`: List of tracker URLs/domains
- `expired_expression`: CEL expression to determine if torrent is expired (optional)
- `not_working_expression`: CEL expression to determine if tracker is not working (optional)

#### Static Configuration Example:
```yaml
trackers:
  - { name: ptp,  required_seed_ratio: 0,    required_seed_days: 0,    urls: ["passthepopcorn.me"] }
  - { name: btn,  required_seed_ratio: 1.01, required_seed_days: 14.1, urls: ["broadcasthe.net"] }
```

#### CEL Expression Configuration Example:
```yaml
trackers:
  - name: iptorrents
    urls: ["bgp.technology", "empirehost.me", "stackoverflow.tech"]
    required_seed_ratio: 1.05
    required_seed_days: 14.5
    expired_expression: |
      (torrent.RequiredSeedRatio > 0 && torrent.Ratio >= torrent.RequiredSeedRatio) ||
      (torrent.RequiredSeedDays > 0 && torrent.SeedDays >= torrent.RequiredSeedDays) ||
      (torrent.SeedDays > 30 && torrent.Ratio >= 1.0)
    not_working_expression: |
      containsAny(torrent.TrackerMessages, [
        "UNREGISTERED", "TORRENT NOT FOUND", "NOT REGISTERED", "DEAD", "BANNED"
      ])
```

#### CEL Expression Functions:
- `torrent.SeedDays`: Seeding time in days
- `torrent.AgeDays`: Age since added in days
- `torrent.ActivityDays`: Days since last activity
- `containsAny(list1, list2)`: Check if any item in list1 contains any item in list2
- `contains(string, substring)`: Check if string contains substring
- `hasTag(tags, tag)`: Check if torrent has specific tag

#### Available Torrent Context:
- **Basic**: Hash, Name, Size, Progress, State, Category, Tags, SavePath, ContentPath
- **Tracker**: Tracker, TrackerName, TrackerStatus, TrackerMessages
- **Timing**: AddedOn, CompletedOn, LastActivity, SeedingTime
- **Transfer**: Ratio, Downloaded, Uploaded
- **Calculated**: SeedDays, AgeDays, ActivityDays
- **Config**: RequiredSeedRatio, RequiredSeedDays

### Global Options

- `-c, --config`: Path to configuration file (default: `/config/config.yaml`)
- `-l, --log-level`: Log level (debug, info, warn, error)

## Usage

### Help

All commands have extensive help with available options:

```bash
qbtools --help
qbtools tagging --help
qbtools reannounce --help
qbtools prune --help
```

### Available Commands

#### Tagging

The tagging command creates useful tags to organize torrents by various criteria:

- `--duplicates`: Tag duplicate torrents
- `--unregistered`: Tag torrents with unregistered status  
- `--not-working`: Tag torrents with non-working trackers
- `--added-on`: Tag torrents based on when they were added
- `--sites`: Tag torrents by tracker domain
- `--cel-mode`: Use CEL expressions from config for dynamic evaluation

**Standard mode (backward compatible):**
```bash
qbtools tagging --duplicates --unregistered --not-working --added-on --sites
```

**CEL mode (dynamic evaluation):**
```bash
qbtools tagging --cel-mode --expired --not-working --sites
```

CEL mode allows you to define complex rules in your configuration file using CEL expressions. This enables:
- Custom expiration criteria beyond simple ratio/time thresholds
- Dynamic tracker status evaluation based on error messages
- Per-tracker customization of rules
- Complex boolean logic combining multiple conditions

#### Reannounce

Automatically reannounce torrents that have problematic trackers:

- `--max-age`: Maximum age of torrents to reannounce in seconds (default: 3600)
- `--max-retries`: Maximum number of reannounce attempts (default: 18)
- `--interval`: Interval between reannouncements in seconds (default: 5)
- `--process-seeding`: Also process seeding torrents

```bash
qbtools reannounce --max-age 7200 --process-seeding
```

#### Prune

Remove torrents based on tag criteria:

- `--include-tag`: Include torrents with these tags (can be used multiple times)
- `--exclude-tag`: Exclude torrents with these tags (can be used multiple times)
- `--dry-run`: Show what would be removed without actually removing

```bash
qbtools prune --include-tag "expired" --include-tag "added:30d" --exclude-tag "site:ptp" --dry-run
```

The prune command uses the tracker configuration from `config.yaml` to determine which torrents meet seeding requirements and can be safely removed.
