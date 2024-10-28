import time
import httpx

from httpx import URL
from qbtools import utils
from typing import Optional, Tuple


def __init__(app, logger):
    logger.info("Starting limiter process...")

    app.sabnzbd_host = parse_sabnzbd_host(app)

    def process():
        qbittorrent_queue, qbittorrent_current_limit = qbittorrent_data(app)
        sabnzbd_queue, sabnzbd_current_limit = sabnzbd_data(app)

        qbittorrent_current_limit = int(qbittorrent_current_limit / 1024 / 1024)
        sabnzbd_current_limit = int(sabnzbd_current_limit / 1024 / 1024)

        logger.debug(
            f"qBittorrent: {qbittorrent_queue} item(s) @ {qbittorrent_current_limit} MB/s"
        )
        logger.debug(
            f"SabNZBD: {sabnzbd_queue} item(s) @ max {sabnzbd_current_limit} MB/s"
        )

        percentage = (
            app.limit_percent
            if qbittorrent_queue and sabnzbd_queue
            else app.max_percent
        )

        limit = int(app.max_line_speed_mbps * percentage)

        if qbittorrent_current_limit != limit:
            app.client.transfer_set_download_limit(limit * 1024 * 1024)
            logger.info(
                f"qbittorrent download limit set to {limit} MB/s "
                f"(was {qbittorrent_current_limit} MB/s)..."
            )

        if sabnzbd_current_limit != limit:
            handle_request(
                url=f"{app.sabnzbd_host}/api",
                method="POST",
                data=dict(
                    apikey=app.sabnzbd_apikey,
                    mode="config",
                    name="speedlimit",
                    value=int(percentage * 100),
                ),
            )
            logger.info(
                f"sabnzbd download limit set to {limit} MB/s "
                f"(was {sabnzbd_current_limit} MB/s)..."
            )

    while True:
        try:
            process()
        except Exception as e:
            logger.error(e)

        time.sleep(app.interval)


def parse_sabnzbd_host(app) -> str:
    url = app.sabnzbd_host
    if not URL(url).host:
        url = (
            f"http://{app.sabnzbd_host}:{app.sabnzbd_port}"
            if app.sabnzbd_port
            else f"http://{app.sabnzbd_host}"
        )
    return url


def qbittorrent_data(app) -> Tuple[int, int]:
    torrents = len(app.client.torrents.info(status_filter="downloading"))
    download_limit = app.client.transfer_download_limit()
    return torrents, download_limit


def sabnzbd_data(app) -> Tuple[int, int]:
    data = handle_request(
        f"{app.sabnzbd_host}/api?apikey={app.sabnzbd_apikey}&mode=queue&output=json"
    )
    return (
        int(data.get("queue", {}).get("noofslots", 0)) if data else 0,
        int(data.get("queue", {}).get("speedlimit_abs", 0)) if data else 0,
    )


def handle_request(
    url: str, method: str = "GET", data: Optional[dict] = None
) -> Optional[dict]:
    response = httpx.request(method=method, url=url, data=data)
    response.raise_for_status()
    return response.json() if method == "GET" else None


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
        action=utils.EnvDefault,
        envvar="SABNZBD_HOST",
        help="The host of the SabNZBD server",
        required=True,
    )
    parser.add_argument(
        "--sabnzbd-port",
        action=utils.EnvDefault,
        envvar="SABNZBD_PORT",
        help="The port of the SabNZBD server",
        required=False,
    )
    parser.add_argument(
        "--sabnzbd-apikey",
        action=utils.EnvDefault,
        envvar="SABNZBD_API_KEY",
        help="The API key for the SabNZBD server",
        required=True,
    )
    parser.add_argument(
        "--max-line-speed-mbps",
        type=float,
        default=100,
        help="The maximum line speed in Mbps",
    )
    parser.add_argument(
        "--limit-percent",
        type=float,
        default=0.5,
        help="The percentage of the line speed to limit to when both are downloading",
    )
    parser.add_argument(
        "--max-percent",
        type=float,
        default=1.0,
        help="The maximum percentage of the line speed to limit to when both are not downloading",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="The interval to check the speeds in seconds",
    )
