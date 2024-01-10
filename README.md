## Upstream

This is an opinionated fork of the upstream project at https://gitlab.com/AlexKM/qbittools.

## Description

qbtools is a feature rich CLI for the management of torrents in qBittorrent.

## Table of contents

- [Upstream](#upstream)
- [Description](#description)
- [Table of contents](#table-of-contents)
- [Installation](#installation)
  - [Docker image](#docker-image)
  - [Building](#building)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Help](#help)
  - [Subcommands](#subcommands)
    - [Tagging](#tagging)
    - [Reannounce](#reannounce)
    - [Orphaned](#orphaned)

## Installation

### Docker image

Run a container with access to host network:

```bash
docker run -it --rm --network host github.com/buroa/qbtools tagging --unregistered
```

### Building

```bash
# clone the repository
git clone https://github.com/buroa/qbtools.git && cd qbtools
# build the image
docker build -t qbtools:latest --pull .
# run a container with the resulting binary and access to host network
docker run -it --rm --network host qbtools reannounce -p 12345
```

## Configuration

You have to specify your password every time with `-P` flag unless you enable `Web UI -> Bypass authentication for clients on localhost` in qBittorrent's settings, because there is no way for qbtools to retrieve it in plaintext.

You also can specify host, port and username manually without a configuration file with `-s`, `-p` and `-U` flags accordingly.

There is also a `config.yaml` file which can be overrideen to add your own indexers and their corresponding requirements.

## Usage

### Help

All commands have extensive help with all available options.

```bash
$ qbtools export -h
usage: qbtools.py reannounce [-h] [--pause-resume] [--process-seeding]
                               [-c /app/config.yaml] [-p 12345] [-s 127.0.0.1] [-U username]
                               [-P password]

options:
  -h, --help            show this help message and exit
  --pause-resume        Will pause/resume torrents that are invalid.
  --process-seeding     Will also process seeding torrents for reannouncements.
  -c /app/config.yaml, --config /app/config.yaml
  -p 12345, --port 12345
                        port
  -s 127.0.0.1, --server 127.0.0.1
                        host
  -U username, --username username
  -P password, --password password
```

### Subcommands

#### Tagging

Create useful tags to group torrents by tracker domains, not working trackers, unregistered torrents and duplicates

```bash
$ qbtools tagging --duplicates --unregistered --not-working --added-on --trackers
```

#### Reannounce

Automatic reannounce on problematic trackers

```bash
$ qbtools reannounce
07:40:40 PM --------------------------
07:40:40 PM [Movie.2020.2160p.WEB-DL.H264-GROUP] is not working, active for 1s, reannouncing...
07:41:20 PM --------------------------
07:41:20 PM [Movie.2020.2160p.WEB-DL.H264-GROUP] has no seeds, active for 78s, reannouncing...
07:41:25 PM --------------------------
07:41:25 PM [Movie.2020.2160p.WEB-DL.H264-GROUP] is active, progress: 0%
07:41:30 PM --------------------------
07:41:30 PM [Movie.2020.2160p.WEB-DL.H264-GROUP] is active, progress: 5.0%
07:41:35 PM --------------------------
07:41:35 PM [Movie.2020.2160p.WEB-DL.H264-GROUP] is active, progress: 11.1%
```

#### Orphaned

Find files no longer associated with any torrent, but still present in download folders (default download folder and folders from all categories). This command will remove orphaned files unless you pass the `--dry-run` flag.

This command is very opinionated on a certian directory structure so use with caution and make sure you run it with the `--dry-run` flag to make sure it won't delete anything unintentional.

This is how I have my paths laid out where `/downloads/qbittorrent/complete` is the default save path in qBittorrent and each folder under it is a category. `Default Torrent Management Mode: Automatic`, `When Torrent Category changed: Relocate`, `When Default Save Path changed: Relocate affected torrents` and `When Category Save Path changed: Relocate affected torrents` is also set. Also make sure you use an incomplete directory that is outside the `/downloads/qbittorrent/complete` directory.

```
/downloads/qbittorrent
└── complete
    ├── cross-seed
    ├── hit-and-runs
    ├── lidarr
    ├── manual
    ├── myanonamouse
    ├── overlord
    ├── prowlarr
    ├── radarr
    ├── redacted
    ├── rifftrax
    └── sonarr
```

```bash
$ qbtools orphaned --ignore-pattern "*_unpackerred" --ignore-pattern "*/manual/*"
```
