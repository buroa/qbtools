#!/usr/bin/env python3

import argparse, logging, sys, pkgutil, collections, os, configparser
from pathlib import Path

if getattr(sys, 'oxidized', False):
    os.environ['PYOXIDIZER'] = '1'

import qbittorrentapi
import commands.add, commands.export, commands.reannounce, commands.update_passkey, commands.tagging, commands.upgrade, commands.unpause

def add_default_args(parser):
    parser.add_argument('-C', '--config', metavar='~/.config/qBittorrent/qBittorrent.conf', default='~/.config/qBittorrent/qBittorrent.conf', required=False)
    parser.add_argument('-p', '--port', metavar='12345', help='port', required=False)
    parser.add_argument('-s', '--server', metavar='127.0.0.1', default='127.0.0.1', help='host', required=False)
    parser.add_argument('-U', '--username', metavar='username', required=False)
    parser.add_argument('-P', '--password', metavar='password', required=False)

def qbit_client(args):
    config = config_values(args.config)

    if args.server is None:
        args.server = config[0]

    if args.port is None:
        args.port = config[1]

    if args.username is None:
        args.username = config[2]

    if args.server is None or args.port is None:
        logger.error('Unable to get qBittorrent host and port automatically, specify config file or host/port manually')
        sys.exit(1)

    client = qbittorrentapi.Client(host=f"{args.server}:{args.port}", username=args.username, password=args.password)

    try:
        client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        logger().error(e)
    return client

logger = logging.getLogger(__name__)

def config_values(path):
    config = configparser.ConfigParser()
    config.read(Path(path).expanduser())

    if not 'Preferences' in config:
        return (None, None, None)

    preferences = config['Preferences']
    host = preferences.get('webui\\address')
    port = preferences.get('webui\\port')
    user = preferences.get('webui\\username')

    return (host, port, user)

def main():
    logging.getLogger("filelock").setLevel(logging.ERROR) # supress lock messages
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%I:%M:%S %p')

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    for cmd in ['add', 'export', 'reannounce', 'update_passkey', 'tagging', 'upgrade', 'unpause']:
        mod = getattr(globals()['commands'], cmd)
        getattr(mod, 'add_arguments')(subparsers)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit()

    mod = getattr(globals()['commands'], args.command)
    cmd = getattr(mod, '__init__')(args, logger)

if __name__ == "__main__":
    main()
