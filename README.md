## Installation

Clone the repository
```
git clone https://gitlab.com/AlexKM/qbit-tools.git ~/qbit-tools
```

Install dependencies (isolated to the current user)
```
cd ~/qbit-tools
pip3 install --user -r requirements.txt
```

## Configuration

All scripts have extensive help with all available options:
```bash
$ ./add.py -h
usage: add.py [-h] -i my.torrent [my.torrent ...] [-o /home/user/downloads]
              [-c mycategory] [-t [mytag [mytag ...]]] [--skip-checking]
              [--add-paused] [--dl-limit DL_LIMIT] [--up-limit UP_LIMIT] -p
              12345 [-s 127.0.0.1] [-U username] [-P password]

optional arguments:
  -h, --help            show this help message and exit
  -i my.torrent [my.torrent ...], --input my.torrent [my.torrent ...]
                        torrents path
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
  -p 12345, --port 12345
                        port
  -s 127.0.0.1, --server 127.0.0.1
                        host
  -U username, --username username
  -P password, --password password
```

Adding torrents from autodl-irssi to qBittorrent (autodl.cfg example):
```
upload-command = ~/qbit-tools/add.py
upload-args = -i $(TorrentPathName) -p 12345 -c music
upload-type = exec
```

Automatic tagging with crontab:
```
*/10 * * * * ~/qbit-tools/tagging.py -p 12345
```

Automatic reannounce on problematic trackers (run in screen/tmux to prevent it from closing when you end a ssh session):
```bash
$ ./reannounce.py -p 12345
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

Update passkey in all matching torrents (all tracker urls that match `--old` parameter):
```bash
$ ./update_passkey.py --old 12345 --new v3rrjmnfxwq3gfrgs9m37dvnfkvdbqnqc -p 10369
2021-01-08 21:38:45,301 INFO:Replaced [https://trackerurl.net/12345/announce] to [https://trackerurl.net/v3rrjmnfxwq3gfrgs9m37dvnfkvdbqnqc/announce] in 10 torrents
```

Export all matching .torrent files by category or tags:
```bash
$ ./export.py -p 12345 -o ./export --category movies --tags tracker.org mytag
01:23:43 PM INFO:Matched 47 torrents
01:23:43 PM INFO:Exported [movies] Fatman.2020.BluRay.1080p.TrueHD.5.1.AVC.REMUX-FraMeSToR [fbef10dc89bf8dff21a401d9304f62b074ffd6af].torrent
01:23:43 PM INFO:Exported [movies] La.Haine.1995.UHD.BluRay.2160p.DTS-HD.MA.5.1.DV.HEVC.REMUX-FraMeSToR [ee5ff82613c7fcd2672e2b60fc64375486f976ba].torrent
01:23:43 PM INFO:Exported [movies] Ip.Man.3.2015.UHD.BluRay.2160p.TrueHD.Atmos.7.1.DV.HEVC.REMUX-FraMeSToR [07da008f9c64fe4927ee18ac5c94292f61098a69].torrent
01:23:43 PM INFO:Exported [movies] Brazil.1985.Director's.Cut.BluRay.1080p.FLAC.2.0.AVC.REMUX-FraMeSToR [988e8749a9d3f07e5d216001efc938b732579c16].torrent
```
