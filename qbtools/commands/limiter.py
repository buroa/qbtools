import time
import requests
import logging
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

def __init__(app, logger):
    logger.info("Starting limiter process...")

    while True:
        qbittorrent_queue, qbittorrent_current_limit = qbittorrent_data(app)
        sabnzbd_queue, sabnzbd_current_limit = sabnzbd_data(app)

        logger.info(f"qBittorrent: {qbittorrent_queue} item(s) @ {qbittorrent_current_limit} MB/s")
        logger.info(f"SabNZBD: {sabnzbd_queue} item(s) @ max {sabnzbd_current_limit} MB/s")

        percentage = app.limit_percent if qbittorrent_queue > 0 and sabnzbd_queue > 0 else app.max_percent

        qbittorrent_updated_limit = int(app.max_line_speed_mbps * percentage * 1024 * 1024)

        if qbittorrent_current_limit != qbittorrent_updated_limit:
            app.client.transfer_set_download_limit(qbittorrent_updated_limit * 1024 * 1024)
            logger.info(f"qbittorrent download limit set to {qbittorrent_updated_limit / 1024 /1024 } MB/s (was {qbittorrent_current_limit} MB/s)...")

        sabnzbd_updated_limit = int(app.max_line_speed_mbps * percentage)

        if sabnzbd_current_limit != sabnzbd_updated_limit:
            handle_request(f'{app.sabnzbd_host}/api', 'POST', {'apikey': app.sabnzbd_apikey, 'mode': 'config', 'name': 'speedlimit', 'value': sabnzbd_updated_limit})
            logger.info(f"sabnzbd download limit set to {sabnzbd_updated_limit} MB/s (was {sabnzbd_current_limit} MB/s)...")

        time.sleep(app.interval)


def add_arguments(command, subparser):
    """
    Description:
        Limit speeds when qBittorrent and SabNZBD are both downloading.
    Usage:
        qbtools.py limiter --help
    """
    parser = subparser.add_parser(command)
    parser.add_argument(
        "--sabnzbd-host",
        type=str,
        required=True,
        help="The host of the SabNZBD server",
    )
    parser.add_argument(
        "--sabnzbd-apikey",
        type=str,
        required=True,
        help="The API key for the SabNZBD server",
    )
    parser.add_argument(
        "--max-line-speed-mbps",
        type=Decimal,
        default=100,
        help="The maximum line speed in Mbps",
    )
    parser.add_argument(
        "--limit-percent",
        type=Decimal,
        default=0.5,
        help="The percentage of the line speed to limit to when both are downloading",
    )
    parser.add_argument(
        "--max-percent",
        type=Decimal,
        default=1.0,
        help="The maximum percentage of the line speed to limit to when both are not downloading",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="The interval to check the speeds in seconds",
    )


def qbittorrent_data(app) -> Tuple[int, int]:
    return (
        len(app.client.torrents.info(status_filter='downloading')),
        app.client.transfer_download_limit() / 1024 / 1024
    )


def sabnzbd_data(app) -> Tuple[int, int]:
    data = handle_request(f'{app.sabnzbd_host}/api?apikey={app.sabnzbd_apikey}&mode=queue&output=json')
    return (
        int(data.get('queue', {}).get('noofslots', 0)) if data else 0,
        int(data.get('queue', {}).get('speedlimit', 0)) if data else 0
    )


def handle_request(url: str, method: str = 'GET', data: Optional[dict] = None) -> Optional[dict]:
    response = requests.post(url, data=data) if method == 'POST' else requests.get(url)
    response.raise_for_status()
    return response.json() if method == 'GET' else None
