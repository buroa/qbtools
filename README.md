## Description

qbittools is a feature rich CLI for the management of torrents in qBittorrent.

## Donate

If you're feeling generous, you can support this project and me:

Ko-fi (PayPal): https://ko-fi.com/U7U46LR9L

By renting a server with my affiliate link: https://clients.walkerservers.com/aff.php?aff=249

Monero: `44ow4aVdjJK7opDHpRsTiXV6hh5y1T7W81phsasJPBcARox7shnWCemDts6rC3icMA6AuBTV4cWR56dFujcLK7P2TYwBQZv`

Many thanks!

## Table of contents

- [Requirements](#requirements)
- [Installation](#installation)
  - [Building binary manually with Docker (optional)](#building-binary-manually-with-docker-optional)
  - [Run as a script (optional)](#run-as-a-script-optional)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Help](#help)
  - [Self-upgrade](#self-upgrade)
  - [Subcommands](#subcommands)
    - [Add](#add)
      - [Operating system limits](#operating-system-limits)
      - [ruTorrent / AutoDL](#rutorrent-autodl)
    - [Unpause](#unpause)
      - [Automatic unpause in qBittorrent](#automatic-unpause-in-qbittorrent)
    - [Tagging](#tagging)
      - [Automatic tagging with Cron](#automatic-tagging-with-cron)
    - [Reannounce](#reannounce)
      - [Reannounce with systemd](#reannounce-with-systemd)
    - [Update passkey](#update-passkey)
    - [Export](#export)
    - [Mover](#mover)
      - [Automatic moving with Cron](#automatic-moving-with-cron)
    - [Orphaned](#orphaned)
  - [FlexGet](#flexget)

## Requirements

* Any usable Linux distribution since binary builds are built with musl and fully static starting from 0.4.0
* git (for self-upgrading)
* ca-certificates (for self-upgrading and connecting to https)

## Installation

Install the latest version with the install script to `/usr/local/bin/qbittools` (root privileges needed)
```bash
curl -Ls https://gitlab.com/AlexKM/qbittools/-/raw/master/install.sh | sudo bash
```

Or at any path you want without any extra privileges, don't forget to add this path to `$PATH` for convenience:
```bash
mkdir -p ~/bin
curl -Ls https://gitlab.com/AlexKM/qbittools/-/raw/master/install.sh | bash -s -- -o ~/bin/qbittools
```

The script creates a temporary directory, retrieves the latest git tag and downloads it's build artifacts that contains the resulting qbittools binary.

### Building binary manually with Docker (optional)
<details><summary>Click to expand</summary>

```bash
# clone the repository
git clone https://gitlab.com/AlexKM/qbittools.git && cd qbittools
# build the image
docker build -t qbittools:latest --pull .
# run a container with the resulting binary and access to host network
docker run -it --rm --network host qbittools reannounce -p 12345
```

</details>

### Run as a script (optional)
<details><summary>Click to expand</summary>

```bash
# clone the repository
git clone https://gitlab.com/AlexKM/qbittools.git && cd qbittools
# create and activate virtual environment
virtualenv -p python3 venv
source venv/bin/activate
# install dependencies
make deps
# use qbittools.py instead of the binary
```

</details>

## Configuration

qBittools doesn't have any configuration files currently. It parses host, port and username from the qBittorrent configuration file located by default at `~/.config/qBittorrent/qBittorrent.conf`, you can specify a different qBittorrent config with `-c` flag. 

You also have to specify your password every time with `-P` flag unless you enable `Web UI -> Bypass authentication for clients on localhost` in qBittorrent's settings, because there is no way for qBittools to retrieve it in plaintext.

You also can specify host, port and username manually without a configuration file with `-s`, `-p` and `-U` flags accordingly.

## Usage

### Help
All commands have extensive help with all available options:

<details><summary>Click to expand</summary>

```bash
$ qbittools export -h
usage: qbittools export [-h] -p 12345 [-s 127.0.0.1] [-U username] [-P password] [-i ~/.local/share/qBittorrent/BT_backup] -o ~/export [-c mycategory] [-t [mytag ...]]

optional arguments:
  -h, --help            show this help message and exit
  -p 12345, --port 12345
                        port
  -s 127.0.0.1, --server 127.0.0.1
                        host
  -U username, --username username
  -P password, --password password
  -i ~/.local/share/qBittorrent/BT_backup, --input ~/.local/share/qBittorrent/BT_backup
                        Path to qBittorrent .torrent files
  -o ~/export, --output ~/export
                        Path to where to save exported torrents
  -c mycategory, --category mycategory
                        Filter by category
  -t [mytag ...], --tags [mytag ...]
                        Filter by tags
```

</details>

### Self-upgrade

Upgrading to the latest version is available with the `upgrade` command (use sudo if it's in a system path):

<details><summary>Click to expand</summary>

```bash
$ qbittools upgrade
07:24:14 PM INFO:Current version: 0.0.0
07:24:14 PM INFO:Latest version: 0.0.1
07:24:14 PM INFO:Update available, this will replace /usr/local/bin/qbittools with a new version.
OK to proceed [Y/N]? y
07:24:16 PM INFO:Downloading https://gitlab.com/AlexKM/qbittools/-/jobs/artifacts/0.0.1/download?job=release to /tmp/tmpapfpoqud/qbittools.zip
100%|██████████████████████████| 23.3M/23.3M [00:00<00:00, 107MiB/s]
07:24:17 PM INFO:Extracted binary to /tmp/tmpapfpoqud/qbittools
07:24:17 PM INFO:Replacing /usr/local/bin/qbittools with /tmp/tmpapfpoqud/qbittools
```

</details>

### Subcommands
#### Add

<details><summary>Click to expand</summary>


Add a single torrent with custom category
```bash
$ qbittools add /path/to/my.torrent -c mycategory
```

Add a folder of torrents and assign multiple tags
```bash
$ qbittools add /path/to/folder -t mytag1 mytag2
```

Add a torrent in paused state and skip hash checking
```bash
$ qbittools add /path/to/my.torrent --add-paused --skip-checking
```

Don't add more torrents if there are more than 3 downloads active while ignoring downloads with speed under 1 MiB/s
```bash
$ qbittools add /path/to/my.torrent --max-downloads 3 --max-downloads-speed-ignore-limit 1024
```

Pause all active torrents temporarily and mark them with `temp_paused` tag while ignoring active uploads with speed under 10 MiB/s (**You have** to configure unpause command in qBittorrent if you want these torrents to be unpaused automatically)
```bash
$ qbittools add /path/to/my.torrent --pause-active --pause-active-upspeed-ignore-limit 10240
```

</details>

##### Operating system limits

If you encounter `too many open files` or `no file descriptors available` errors while adding a lot of torrents, you can try to bypass it with simple shell commands, this will add torrents one by one:
```bash
IFS=$'\n' find /path/to/your/torrents/ -maxdepth 1 -type f -name "*.torrent" -exec qbittools add {} --skip-checking \;
```

##### ruTorrent / AutoDL
Adding torrents from autodl-irssi to qBittorrent using ruTorrent:
```
Action = Run Program
Command = /usr/local/bin/qbittools
Arguments = add $(TorrentPathName) -c music
```

#### Unpause
Only useful if you pause torrents automatically with `--pause-active` parameters from add command.

Resume all torrents with `temp_paused` tag if there are no active downloads while ignoring slow downloads under 10 MiB/s
```bash
$ qbittools unpause -d 10240
```

##### Automatic unpause in qBittorrent

Check `Run external program on torrent completion` in the settings and use tool with an absolute path:
```
/usr/local/bin/qbittools unpause -d 10240
```

#### Tagging
Create useful tags to group torrents by tracker domains, not working trackers, unregistered torrents and duplicates
```bash
$ qbittools tagging --duplicates --unregistered --not-working --added-on --trackers
```

##### Automatic tagging with Cron
Execute every 10 minutes (`crontab -e` and add this entry)
```
*/10 * * * * /usr/local/bin/qbittools tagging --duplicates --unregistered --not-working --added-on --trackers
```

#### Reannounce
Automatic reannounce on problematic trackers (run in screen/tmux to prevent it from closing when you end a ssh session):

<details><summary>Click to expand</summary>


```bash
$ qbittools reannounce
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

</details>

##### Reannounce with systemd
Reannounce can be executed and restarted on problems automatically by systemd. Create a new service at `/etc/systemd/system/` with the following contents:

<details><summary>Click to expand</summary>

```ini
[Unit]
Description=qbittools reannounce
After=qbittorrent@%i.service

[Service]
User=%i
Group=%i
ExecStart=/usr/local/bin/qbittools reannounce

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

</details>

Restart the daemon with `systemctl daemon-reload` and start the service with `systemctl start qbittools-reannounce@username` by replacing username with the user you want to run it from. Check service logs with `journalctl -u qbittools-reannounce@username.service` if necessary.

#### Update passkey
Update passkey in all matching torrents (all tracker urls that match `--old` parameter):
```bash
$ qbittools update_passkey --old 12345 --new v3rrjmnfxwq3gfrgs9m37dvnfkvdbqnqc
2021-01-08 21:38:45,301 INFO:Replaced [https://trackerurl.net/12345/announce] to [https://trackerurl.net/v3rrjmnfxwq3gfrgs9m37dvnfkvdbqnqc/announce] in 10 torrents
```

#### Export
Export all matching .torrent files by category or tags:

<details><summary>Click to expand</summary>


```bash
$ qbittools export -o ./export --category movies --tags tracker.org mytag
01:23:43 PM INFO:Matched 47 torrents
01:23:43 PM INFO:Exported [movies] Fatman.2020.BluRay.1080p.TrueHD.5.1.AVC.REMUX-FraMeSToR [fbef10dc89bf8dff21a401d9304f62b074ffd6af].torrent
01:23:43 PM INFO:Exported [movies] La.Haine.1995.UHD.BluRay.2160p.DTS-HD.MA.5.1.DV.HEVC.REMUX-FraMeSToR [ee5ff82613c7fcd2672e2b60fc64375486f976ba].torrent
01:23:43 PM INFO:Exported [movies] Ip.Man.3.2015.UHD.BluRay.2160p.TrueHD.Atmos.7.1.DV.HEVC.REMUX-FraMeSToR [07da008f9c64fe4927ee18ac5c94292f61098a69].torrent
01:23:43 PM INFO:Exported [movies] Brazil.1985.Director's.Cut.BluRay.1080p.FLAC.2.0.AVC.REMUX-FraMeSToR [988e8749a9d3f07e5d216001efc938b732579c16].torrent
```

</details>

#### Mover
Useful for those who want to move torrents to different categories over time. Combined with enabled Automatic Torrent Management this will move files from one folder to another.

Move torrents inactive for more than 60 seconds and completed more than 60 minutes ago from categories `tracker1` and `tracker2` to category `lts` 
```bash
$ qbittools mover tracker1 tracker2 -d lts
```

Move torrents inactive for more than 600 seconds and completed more than 30 minutes ago from category `racing` to category `lts` 
```bash
$ qbittools mover racing -d lts --completion-threshold 30 --active-threshold 600
```

##### Automatic moving with Cron
Execute every 10 minutes (`crontab -e` and add this entry)
```
*/10 * * * * /usr/local/bin/qbittools mover racing -d lts
```

#### Orphaned

Find files no longer associated with any torrent, but still present in download folders (default download folder and folders from all categories). This command will remove orphaned files if you confirm it and also clean up all empty folders. _Be careful while removing a lot of files if you use these folders from other torrent client._

```bash
$ qbittools orphaned
```

### FlexGet

qbittools can be used together with FlexGet via `exec` plugin, configuration example:
```yml
taskname:
  rss:
    url: https://site/feed.rss
    all_entries: no
  seen:
    local: yes
  accept_all: yes
  download:
    path: ~/torrents/rss/
    overwrite: yes
  exec:
    auto_escape: yes
    fail_entries: yes
    on_output:
      for_accepted:
        - qbittools add "{{location}}" -c books --rename "{{title}}" --content-layout Subfolder
```
