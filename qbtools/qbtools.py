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
        "-c",
        "--config",
        default="/config/config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "-s",
        "--server",
        action=utils.EnvDefault,
        envvar="QBITTORRENT_HOST",
        help="qBittorrent server address",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--port",
        action=utils.EnvDefault,
        envvar="QBITTORRENT_PORT",
        help="qBittorrent server port",
        required=True,
    )
    parser.add_argument(
        "-U",
        "--username",
        action=utils.EnvDefault,
        envvar="QBITTORRENT_USER",
        help="Username for qBittorrent",
        required=False,
    )
    parser.add_argument(
        "-P",
        "--password",
        action=utils.EnvDefault,
        envvar="QBITTORRENT_PASS",
        help="Password for qBittorrent",
        required=False,
    )


def load_commands(subparsers):
    directory = "commands"

    def load_command(command):
        try:
            mod = importlib.import_module(f"{directory}.{command}")
            mod.add_arguments(command, subparsers)
            subparser = subparsers.choices.get(command)
            if subparser:
                add_default_args(subparser)
        except ImportError:
            logger.error(f"Error loading module: {command}", exc_info=True)
            sys.exit(1)
        else:
            globals()[command] = mod

    for cmd in os.listdir(f"{os.path.dirname(__file__)}/{directory}"):
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
    logging.getLogger("httpx").setLevel(logging.ERROR)  # Suppress httpx messages
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%I:%M:%S %p",
    )

    parser = argparse.ArgumentParser(description="qBittorrent API Client")
    subparsers = parser.add_subparsers(dest="command")
    load_commands(subparsers)  # Load all commands
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
