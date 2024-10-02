#!/usr/bin/env python3

import os
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
        help="qBittorrent server address"
    )
    parser.add_argument(
        "-p", "--port",
        help="qBittorrent server port"
    )
    parser.add_argument(
        "-U", "--username",
        help="Username for qBittorrent"
    )
    parser.add_argument(
        "-P", "--password",
        help="Password for qBittorrent"
    )

def qbit_client(app):
    if not app.server or not app.port:
        logger.error("Server and port must be specified.")
        sys.exit(1)

    client = qbittorrentapi.Client(
        host=f"{app.server}:{app.port}",
        username=app.username,
        password=app.password,
    )

    try:
        client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        logger.error(f"Login failed: {e}")
        sys.exit(1)

    return client

def get_config(app, key=None, default=None):
    try:
        with open(app.config, "r") as stream:
            config = yaml.safe_load(stream)
    except FileNotFoundError:
        logger.warning(f"Configuration file not found: {app.config}")
        config = {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        sys.exit(1)

    return config.get(key, default) if key else config

def main():
    # Configure logging
    logging.getLogger("filelock").setLevel(logging.ERROR)  # Suppress lock messages
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%I:%M:%S %p",
    )

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="qBittorrent API Client")
    add_default_args(parser)
    subparsers = parser.add_subparsers(dest="command")

    # Dynamically load command modules
    commands_dir = "commands"
    if not os.path.isdir(commands_dir):
        logger.error(f"Commands directory not found: {commands_dir}")
        sys.exit(1)

    for cmd in os.listdir(commands_dir):
        if cmd.endswith(".py"):
            name = cmd[:-3]
            try:
                mod = importlib.import_module(f"commands.{name}")
                mod.add_arguments(subparsers)
            except ImportError as e:
                logger.error(f"Error loading module '{name}': {e}")
                sys.exit(1)

    app = parser.parse_args()

    # If no command is specified, display help
    if not app.command:
        parser.print_help()
        sys.exit(1)

    # Initialize qBittorrent client
    app.client = qbit_client(app)

    # Load configuration
    app.config = get_config(app)

    # Execute the specified command
    mod = globals().get(app.command)
    if not mod:
        logger.error(f"Command not found: {app.command}")
        sys.exit(1)

    try:
        mod.__init__(app, logger)
    except Exception as e:
        logger.error(f"Error executing command '{app.command}': {e}")
        sys.exit(1)
    finally:
        app.client.auth_log_out()

if __name__ == "__main__":
    main()
