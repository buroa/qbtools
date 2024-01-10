#!/usr/bin/env python3

import argparse, logging, yaml, sys
import qbittorrentapi
import utils

import commands.orphaned, \
       commands.prune, \
       commands.reannounce, \
       commands.tagging

logger = logging.getLogger(__name__)

def add_default_args(parser):
    parser.add_argument("-c", "--config", metavar="/app/config.yaml", default="/app/config.yaml", required=False)
    parser.add_argument("-s", "--server", metavar="127.0.0.1", help="host", required=False)
    parser.add_argument("-p", "--port", metavar="12345", help="port", required=False)
    parser.add_argument("-U", "--username", metavar="username", required=False)
    parser.add_argument("-P", "--password", metavar="password", required=False)

def qbit_client(args):
    if args.server is None or args.port is None:
        logger.error("Please specify a server and port to connect to.")
        sys.exit(1)

    client = qbittorrentapi.Client(
        host=f"{args.server}:{args.port}",
        username=args.username,
        password=args.password,
    )

    try:
        client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        logger.error(e)

    return client

def get_config(args, key = None, default = None):
    config = {}

    with open(args.config, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            logger.error(e)

    if key:
        config = config.get(key, default)

    return config

def main():
    logging.getLogger("filelock").setLevel(logging.ERROR) # supress lock messages
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s:%(message)s",
        datefmt="%I:%M:%S %p",
    )

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    for cmd in ["orphaned", "prune", "reannounce", "tagging"]:
        mod = getattr(globals()["commands"], cmd)
        getattr(mod, "add_arguments")(subparsers)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit()

    mod = getattr(globals()["commands"], args.command)
    cmd = getattr(mod, "__init__")(args, logger)

if __name__ == "__main__":
    main()
