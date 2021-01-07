## Installation

Clone the repository
```
git clone https://gitlab.com/AlexKM/qbit-tools.git ~/
```

Install dependencies (isolated to the current user)
```
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
