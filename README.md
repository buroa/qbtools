## Requirements

`git`, `gcc` (>= 4.2.0), `glibc` (>= 2.25)

Minimum Linux Distro Versions: Debian 10, Fedora 26, OpenSUSE 15.0, RHEL 8, Ubuntu 18.04

## Installation

Install the latest version with the install script to `/usr/local/bin/qbittools` (root privileges needed)
```bash
curl -Ls https://gitlab.com/AlexKM/qbittools/-/raw/master/install.sh | sudo bash
```

Or at any path you want without any extra privileges, don't forget to add this path to `$PATH` for convenience:
```bash
curl -Ls https://gitlab.com/AlexKM/qbittools/-/raw/master/install.sh | bash -s -- -o ~/bin/qbittools
```

The script creates a temporary directory, retrieves the latest git tag and downloads it's build artifacts that contains the resulting qbittools binary.

### Building binary manually with Docker (optional)
```bash
# clone the repository
git clone https://gitlab.com/AlexKM/qbittools.git && cd qbittools
# build the image
docker build -t qbittools:latest --pull .
# run a container with the resulting binary and access to host network
docker run -it --rm --network host qbittools reannounce -p 12345
```

### Run as a script (optional)

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

### Self-upgrade

Upgrading to the latest version is available with the `upgrade` command (use sudo if it's in a system path):
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

## Usage

### Help
All commands have extensive help with all available options:
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

### Subcommands
#### Add

##### Examples
Add a single torrent with custom category
```bash
$ qbittools add -p 12345 /path/to/my.torrent -c mycategory
```

Add a folder of torrents and assign multiple tags
```bash
$ qbittools add -p 12345 /path/to/folder -t mytag1 mytag2
```

Add a torrent in paused state and skip hash checking
```bash
$ qbittools add -p 12345 /path/to/my.torrent --add-paused --skip-checking
```

Don't add more torrents if there are more than 3 downloads active while ignoring downloads with speed under 1 MiB/s
```bash
$ qbittools add -p 12345 /path/to/my.torrent --max-downloads 3 --max-downloads-speed-ignore-limit 1024
```

Pause all active torrents temporarily and mark them with `temp_paused` tag while ignoring active downloads with speed under 1 MiB/s and active uploads with speed under 10 MiB/s (**You have** to configure unpause command in qBittorrent if you want these torrents to be unpaused automatically)
```bash
$ qbittools add -p 12345 /path/to/my.torrent --pause-active --pause-active-dlspeed-ignore-limit 1024 --pause-active-upspeed-ignore-limit 10240
```

##### ruTorrent / AutoDL
Adding torrents from autodl-irssi to qBittorrent using ruTorrent:
```
Action = Run Program
Command = /usr/local/bin/qbittools
Arguments = add -p 12345 $(TorrentPathName) -c music
```

#### Unpause
Only useful if you pause torrents automatically with `--pause-active` parameters from add command.

##### Examples
Resume all torrents with `temp_paused` tag if there are no active downloads while ignoring slow downloads under 10 MiB/s
```bash
$ qbittools unpause -p 12345 -d 10240
```

##### Automatic unpause in qBittorrent

Check `Run external program on torrent completion` in the settings and use tool with an absolute path:
```
/usr/local/bin/qbittools unpause -p 12345 -d 10240
```

#### Tagging
##### Examples
Create useful tags to group torrents by tracker domains, not working trackers, unregistered torrents and duplicates
```bash
$ qbittools tagging -p 12345
```

##### Automatic tagging with Cron
Execute every 10 minutes (`crontab -e` and add this entry)
```
*/10 * * * * /usr/local/bin/qbittools tagging -p 12345
```

#### Reannounce
Automatic reannounce on problematic trackers (run in screen/tmux to prevent it from closing when you end a ssh session):
```bash
$ qbittools reannounce -p 12345
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

#### Update passkey
Update passkey in all matching torrents (all tracker urls that match `--old` parameter):
```bash
$ qbittools update_passkey -p 12345 --old 12345 --new v3rrjmnfxwq3gfrgs9m37dvnfkvdbqnqc
2021-01-08 21:38:45,301 INFO:Replaced [https://trackerurl.net/12345/announce] to [https://trackerurl.net/v3rrjmnfxwq3gfrgs9m37dvnfkvdbqnqc/announce] in 10 torrents
```

#### Export
Export all matching .torrent files by category or tags:
```bash
$ qbittools export -p 12345 -o ./export --category movies --tags tracker.org mytag
01:23:43 PM INFO:Matched 47 torrents
01:23:43 PM INFO:Exported [movies] Fatman.2020.BluRay.1080p.TrueHD.5.1.AVC.REMUX-FraMeSToR [fbef10dc89bf8dff21a401d9304f62b074ffd6af].torrent
01:23:43 PM INFO:Exported [movies] La.Haine.1995.UHD.BluRay.2160p.DTS-HD.MA.5.1.DV.HEVC.REMUX-FraMeSToR [ee5ff82613c7fcd2672e2b60fc64375486f976ba].torrent
01:23:43 PM INFO:Exported [movies] Ip.Man.3.2015.UHD.BluRay.2160p.TrueHD.Atmos.7.1.DV.HEVC.REMUX-FraMeSToR [07da008f9c64fe4927ee18ac5c94292f61098a69].torrent
01:23:43 PM INFO:Exported [movies] Brazil.1985.Director's.Cut.BluRay.1080p.FLAC.2.0.AVC.REMUX-FraMeSToR [988e8749a9d3f07e5d216001efc938b732579c16].torrent
```
