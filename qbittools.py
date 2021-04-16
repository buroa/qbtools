#!/usr/bin/env python3

import argparse, logging, sys, pkgutil, collections, os

if getattr(sys, 'oxidized', False):
    os.environ['PYOXIDIZER'] = '1'

import qbittorrentapi
import commands.add, commands.export, commands.reannounce, commands.update_passkey, commands.tagging, commands.upgrade, commands.unpause

def add_default_args(parser):
    parser.add_argument('-p', '--port', metavar='12345', help='port', required=True)
    parser.add_argument('-s', '--server', metavar='127.0.0.1', default='127.0.0.1', help='host', required=False)
    parser.add_argument('-U', '--username', metavar='username', required=False)
    parser.add_argument('-P', '--password', metavar='password', required=False)

def qbit_client(server, port, username, password):
    client = qbittorrentapi.Client(host=f"{server}:{port}", username=username, password=password)

    try:
        client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        logger().error(e)
    return client

def logger():
    return logging.getLogger(__name__)

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
    cmd = getattr(mod, '__init__')(args, logger())

if __name__ == "__main__":
    main()
