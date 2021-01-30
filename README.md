## Installation

Download the latest release from [the releases page](https://gitlab.com/AlexKM/qbitools/-/releases) (Other -> `qbitools`)
```bash
# use sudo if not under root (example url)
curl -L https://gitlab.com/api/v4/projects/23524151/jobs/996560191/artifacts/qbitools -o /usr/local/bin/qbitools
# give executable permissions
chmod +x /usr/local/bin/qbitools
```

Done!

### Building manually (optional)
```bash
# clone the repository
git clone https://gitlab.com/AlexKM/qbitools.git && cd qbitools
# install dependencies and build the resulting binary to qbitools
make all
# install the binary to /usr/local/bin/qbitools
make install
```

### Run as a script (optional)

```bash
# clone the repository
git clone https://gitlab.com/AlexKM/qbitools.git && cd qbitools
# install dependencies
make deps
# use qbitools.py instead of a binary
```

## Configuration

### Help
All commands have extensive help with all available options:
```bash
$ qbitools -h
usage: qbitools [-h] -p 12345 [-s 127.0.0.1] [-U username] [-P password]
                {add,export,reannounce,tagging,update_passkey} ...

positional arguments:
  {add,export,reannounce,tagging,update_passkey}

optional arguments:
  -h, --help            show this help message and exit
  -p 12345, --port 12345
                        port
  -s 127.0.0.1, --server 127.0.0.1
                        host
  -U username, --username username
  -P password, --password password
```

### Subcommands
Use a subcommand help to get further options:
```bash
$ qbitools add -h
usage: qbitools add [-h] [-o /home/user/downloads] [-c mycategory]
                    [-t [mytag [mytag ...]]] [--skip-checking] [--add-paused]
                    [--dl-limit DL_LIMIT] [--up-limit UP_LIMIT]
                    my.torrent [my.torrent ...]

positional arguments:
  my.torrent            torrents path

optional arguments:
  -h, --help            show this help message and exit
  -o /home/user/downloads, --output /home/user/downloads
                        download folder
  -c mycategory, --category mycategory
                        category to assign
  -t [mytag [mytag ...]], --tags [mytag [mytag ...]]
                        tags to assign, qBit 4.3.2+
  --skip-checking       skip checking
  --add-paused          add paused
  --dl-limit DL_LIMIT   download limit in KiB/s
  --up-limit UP_LIMIT   upload limit in KiB/s
```

```bash
$ qbitools export -h
usage: qbitools export [-h] [-i ~/.local/share/qBittorrent/BT_backup] -o
                       ~/export [-c mycategory] [-t [mytag [mytag ...]]]

optional arguments:
  -h, --help            show this help message and exit
  -i ~/.local/share/qBittorrent/BT_backup, --input ~/.local/share/qBittorrent/BT_backup
                        Path to qBittorrent .torrent files
  -o ~/export, --output ~/export
                        Path to where to save exported torrents
  -c mycategory, --category mycategory
                        Filter by category
  -t [mytag [mytag ...]], --tags [mytag [mytag ...]]
                        Filter by tags
```

### Add command
Adding torrents from autodl-irssi to qBittorrent using ruTorrent:
```
Action = Run Program
Command = /usr/local/bin/qbitools
Arguments = -p 12345 add $(TorrentPathName) -c music
```

### Tagging command
Automatic tagging with crontab:
```
*/10 * * * * /usr/local/bin/qbitools -p 12345 tagging
```

### Reannounce command
Automatic reannounce on problematic trackers (run in screen/tmux to prevent it from closing when you end a ssh session):
```bash
$ qbitools -p 12345 reannounce
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

### Update passkey command
Update passkey in all matching torrents (all tracker urls that match `--old` parameter):
```bash
$ qbitools -p 12345 update_passkey --old 12345 --new v3rrjmnfxwq3gfrgs9m37dvnfkvdbqnqc
2021-01-08 21:38:45,301 INFO:Replaced [https://trackerurl.net/12345/announce] to [https://trackerurl.net/v3rrjmnfxwq3gfrgs9m37dvnfkvdbqnqc/announce] in 10 torrents
```

### Export command
Export all matching .torrent files by category or tags:
```bash
$ qbitools -p 12345 export -o ./export --category movies --tags tracker.org mytag
01:23:43 PM INFO:Matched 47 torrents
01:23:43 PM INFO:Exported [movies] Fatman.2020.BluRay.1080p.TrueHD.5.1.AVC.REMUX-FraMeSToR [fbef10dc89bf8dff21a401d9304f62b074ffd6af].torrent
01:23:43 PM INFO:Exported [movies] La.Haine.1995.UHD.BluRay.2160p.DTS-HD.MA.5.1.DV.HEVC.REMUX-FraMeSToR [ee5ff82613c7fcd2672e2b60fc64375486f976ba].torrent
01:23:43 PM INFO:Exported [movies] Ip.Man.3.2015.UHD.BluRay.2160p.TrueHD.Atmos.7.1.DV.HEVC.REMUX-FraMeSToR [07da008f9c64fe4927ee18ac5c94292f61098a69].torrent
01:23:43 PM INFO:Exported [movies] Brazil.1985.Director's.Cut.BluRay.1080p.FLAC.2.0.AVC.REMUX-FraMeSToR [988e8749a9d3f07e5d216001efc938b732579c16].torrent
```
