#!/usr/bin/env python3

import os
import utils
import importlib
import qbittorrentapi
import argparse
import logging
import yaml
import sys

logger = logging.getLogger(__name__)


def add_default_args(parser):
    parser.add_argument(
        "-c", "--config",
        default="/config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "-s", "--server",
        help="qBittorrent server address",
        required=True
    )
    parser.add_argument(
        "-p", "--port",
        help="qBittorrent server port",
        required=True
    )
    parser.add_argument(
        "-U", "--username",
        help="Username for qBittorrent"
    )
    parser.add_argument(
        "-P", "--password",
        help="Password for qBittorrent"
    )


def load_commands(subparsers):
    def load_command(name):
        try:
            mod = importlib.import_module(f"commands.{name}")
            mod.add_arguments(subparsers)
            subparser = subparsers.choices.get(name)
            if subparser:
                add_default_args(subparser)
        except ImportError:
            logger.error(f"Error loading module: {name}", exc_info=True)
            sys.exit(1)
        else:
            globals()[name] = mod

    for cmd in os.listdir(f"{os.path.dirname(__file__)}/commands"):
        if cmd.startswith("__") or not cmd.endswith(".py"):
            continue
        load_command(cmd[:-3])


def qbit_client(app):
    client = qbittorrentapi.Client(
        host=f"{app.server}:{app.port}",
        username=app.username,
        password=app.password,
    )

    try:
        client.auth_log_in()
    except qbittorrentapi.APIConnectionError:
        logger.error("Error connecting to qBittorrent", exc_info=True)
        sys.exit(1)
    except qbittorrentapi.LoginFailed:
        logger.error("Login failed to qBittorrent", exc_info=True)
        sys.exit(1)
    else:
        return client


def get_config(app):
    try:
        with open(app.config, "r") as stream:
            config = yaml.safe_load(stream)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {app.config}", exc_info=True)
        sys.exit(1)
    except yaml.YAMLError:
        logger.error(f"Error parsing configuration file: {app.config}", exc_info=True)
        sys.exit(1)
    else:
        return config


def main():
    logging.getLogger("filelock").setLevel(logging.ERROR)  # Suppress lock messages
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%I:%M:%S %p",
    )

    parser = argparse.ArgumentParser(description="qBittorrent API Client")
    subparsers = parser.add_subparsers(dest="command")
    load_commands(subparsers) # Load all commands

    app = parser.parse_args()

    if not app.command:
        parser.print_help()
        sys.exit(1)

    app.client = qbit_client(app)
    app.config = get_config(app)

    try:
        mod = globals()[app.command]
        mod.__init__(app, logger)
    except Exception:
        logger.error(f"Error executing command: {app.command}", exc_info=True)
        sys.exit(1)
    finally:
        app.client.auth_log_out()

if __name__ == "__main__":
    main()
