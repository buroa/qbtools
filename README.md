# qbtools

## Description

qbtools is a feature rich CLI for the management of torrents in qBittorrent, written in Go 1.24 using the [github.com/autobrr/go-qbittorrent](https://github.com/autobrr/go-qbittorrent) client.

## Features

- **Tagging**: Automatically tag torrents based on tracker domains, status, duplicates, and age
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
- `ratio`: Minimum ratio requirement
- `days`: Minimum seeding time in days
- `urls`: List of tracker URLs/domains

Example configuration:
```yaml
trackers:
  - { name: ptp,  ratio: 0,    days: 0,    urls: ["passthepopcorn.me"] }
  - { name: btn,  ratio: 1.01, days: 14.1, urls: ["broadcasthe.net"] }
```

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

```bash
qbtools tagging --duplicates --unregistered --not-working --added-on --sites
```

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
