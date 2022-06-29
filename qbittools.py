#!/usr/bin/env python3

import argparse, logging, sys, pkgutil, collections, os, configparser
import ipaddress
from typing import NamedTuple
import pathlib3x as pathlib

if getattr(sys, 'oxidized', False):
    os.environ['PYOXIDIZER'] = '1'

import qbittorrentapi
import commands.add, commands.export, commands.reannounce, commands.update_passkey, commands.tagging, commands.upgrade, commands.unpause, commands.mover, commands.orphaned

class QbitConfig(NamedTuple):
    host: str
    port: str
    username: str
    save_path: pathlib.Path

logger = logging.getLogger(__name__)
config = None

def add_default_args(parser):
    parser.add_argument('-C', '--config', metavar='~/.config/qBittorrent/qBittorrent.conf', default='~/.config/qBittorrent/qBittorrent.conf', required=False)
    parser.add_argument('-p', '--port', metavar='12345', help='port', required=False)
    parser.add_argument('-s', '--server', metavar='127.0.0.1', help='host', required=False)
    parser.add_argument('-U', '--username', metavar='username', required=False)
    parser.add_argument('-P', '--password', metavar='password', required=False)

def qbit_client(args):
    global config

    config = config_values(args.config)

    if args.server is None:
        args.server = config.host

    if args.port is None:
        args.port = config.port

    if args.username is None:
        args.username = config.username

    if args.server is None or args.port is None:
        logger.error('Unable to get qBittorrent host and port automatically, specify config file or host/port manually, see help with -h')
        sys.exit(1)

    client = qbittorrentapi.Client(host=f"{args.server}:{args.port}", username=args.username, password=args.password)

    try:
        client.auth_log_in()

        if config.save_path is None and not client.application.preferences.save_path is None:
            config = QbitConfig(config.host, config.port, config.username, pathlib.Path(client.application.preferences.save_path))
    except qbittorrentapi.LoginFailed as e:
        logger.error(e)
    return client

def config_values(path):
    config = configparser.ConfigParser()
    config.read(pathlib.Path(path).expanduser())

    if not 'Preferences' in config:
        return QbitConfig(None, None, None, None)

    preferences = config['Preferences']
    host = preferences.get('webui\\address')

    if not host is None:
        try:
            host = ipaddress.ip_address(host)
        except ValueError as e:
            host = '127.0.0.1'

    port = preferences.get('webui\\port')
    user = preferences.get('webui\\username')
    save_path = preferences.get('downloads\\savepath')

    if not save_path is None:
        save_path = pathlib.Path(save_path)

    return QbitConfig(host, port, user, save_path)

def main():
    global config

    logging.getLogger("filelock").setLevel(logging.ERROR) # supress lock messages
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%I:%M:%S %p')

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    for cmd in ['add', 'export', 'reannounce', 'update_passkey', 'tagging', 'upgrade', 'unpause', 'mover', 'orphaned']:
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
