import qbtools
import tldextract
import collections

from datetime import datetime
from qbittorrentapi import TrackerStatus


DEFAULT_TAGS = [
    "activity:",
    "added:",
    "dupe",
    "expired",
    "not-linked",
    "not-working",
    "unregistered",
    "tracker-down",
    "domain:",
    "site:",
]

UNREGISTERED_MATCHES = [
    "UNREGISTERED",
    "TORRENT NOT FOUND",
    "TORRENT IS NOT",
    "NOT REGISTERED",
    "NOT EXIST",
    "UNKNOWN TORRENT",
    "TRUMP",
    "RETITLED",
    "TRUNCATED",
    "INFOHASH NOT FOUND", # blutopia
    "TORRENT HAS BEEN DELETED", # blutopia
    "DEAD",
    "DUPE",
    "COMPLETE SEASON UPLOADED",
    "PROBLEM",
    "SPECIFICALLY BANNED",
    "OTHER",
    "NUKED",
    "INVALID INFOHASH",
]

MAINTENANCE_MATCHES = [
    "DOWN",
    "UNREACHABLE",
    "BAD GATEWAY",
    "TRACKER UNAVILABLE",
]


def __init__(args, logger):
    logger.info(f"Tagging torrents in qBittorrent...")

    client = qbtools.qbit_client(args)
    trackers = qbtools.get_config(args, "trackers", [])

    extractTLD = tldextract.TLDExtract(cache_dir=None)
    today = datetime.today()
    tag_hashes = collections.defaultdict(list)
    tag_sizes = collections.defaultdict(int)
    content_paths = []
    filtered_torrents = client.torrents.info()

    exclude_categories = [i for s in args.exclude_category for i in s]
    if exclude_categories:
        filtered_torrents = list(
            filter(lambda x: x.category not in exclude_categories, filtered_torrents)
        )

    exclude_tags = [i for s in args.exclude_tag for i in s]
    if exclude_tags:
        filtered_torrents = list(
            filter(
                lambda x: any(y not in x.tags for y in exclude_tags), filtered_torrents
            )
        )

    # Gather items to tag in qBittorrent
    for t in filtered_torrents:
        tags_to_add = []

        filtered_trackers = (
            list(filter(lambda s: not s.tier == -1, t.trackers))
            if t.properties.is_private
            else t.trackers
        )
        if not filtered_trackers:
            continue
        domain = extractTLD(
            sorted(filtered_trackers, key=lambda x: x.url)[0].url
        ).registered_domain
        tracker = qbtools.utils.filter_tracker_by_domain(domain, trackers)

        if args.added_on:
            added_on = datetime.fromtimestamp(t.added_on)
            diff = today - added_on

            if diff.days == 0:
                tags_to_add.append("added:24h")
            elif diff.days <= 7:
                tags_to_add.append("added:7d")
            elif diff.days <= 30:
                tags_to_add.append("added:30d")
            elif diff.days <= 180:
                tags_to_add.append("added:180d")
            elif diff.days > 180:
                tags_to_add.append("added:>180d")

        if args.last_activity:
            last_activity = datetime.fromtimestamp(t.last_activity)
            diff = datetime.today() - last_activity

            if t.last_activity == -1:
                tags_to_add.append("activity:never")
            elif diff.days == 0:
                tags_to_add.append("activity:24h")
            elif diff.days <= 7:
                tags_to_add.append("activity:7d")
            elif diff.days <= 30:
                tags_to_add.append("activity:30d")
            elif diff.days <= 180:
                tags_to_add.append("activity:180d")
            elif diff.days > 180:
                tags_to_add.append("activity:>180d")

        if args.sites:
            if tracker:
                tags_to_add.append(f"site:{tracker['name']}")
            else:
                tags_to_add.append(f"site:unmapped")

        if args.domains:
            tags_to_add.append(f"domain:{domain}")

        if args.unregistered or args.tracker_down or args.not_working:
            if not any(s.status == TrackerStatus.WORKING for s in filtered_trackers):
                tracker_messages = [z.msg.upper() for z in filtered_trackers]
                if args.unregistered and any(x in msg for msg in tracker_messages for x in UNREGISTERED_MATCHES):
                    tags_to_add.append("unregistered")
                elif args.tracker_down and any(x in msg for msg in tracker_messages for x in MAINTENANCE_MATCHES):
                    tags_to_add.append("tracker-down")
                elif args.not_working:
                    tags_to_add.append("not-working")

        if args.expired and tracker and t.state_enum.is_complete:
            if (
                tracker["required_seed_ratio"] != 0
                and t.ratio >= tracker["required_seed_ratio"]
            ):
                tags_to_add.append("expired")
            elif tracker[
                "required_seed_days"
            ] != 0 and t.seeding_time >= qbtools.utils.seconds(
                tracker["required_seed_days"]
            ):
                tags_to_add.append("expired")

        if args.duplicates:
            match = [
                (infohash, path, size)
                for infohash, path, size in content_paths
                if path == t.content_path and not t.content_path == t.save_path
            ]
            if match:
                tags_to_add.append("dupe")
                tag_hashes["dupe"].append(match[0][0])
                if args.size:
                    tag_sizes["dupe"] += match[0][2]

            content_paths.append((t.hash, t.content_path, t.size))

        if args.not_linked and not qbtools.utils.is_linked(t.content_path):
            tags_to_add.append("not-linked")

        for tag in tags_to_add:
            tag_hashes[tag].append(t.hash)
            if args.size:
                tag_sizes[tag] += t.size

    # Remove old tags
    default_tags = list(
        filter(
            lambda tag: any(tag.lower().startswith(x.lower()) for x in DEFAULT_TAGS),
            client.torrents_tags(),
        )
    )
    if default_tags:
        hashes = list(map(lambda t: t.hash, filtered_torrents))
        client.torrents_remove_tags(tags=default_tags, torrent_hashes=hashes)
        empty_tags = list(
            filter(
                lambda tag: len(
                    list(filter(lambda t: tag in t.tags, client.torrents.info()))
                )
                == 0,
                default_tags,
            )
        )
        logger.info(f"Removing {len(empty_tags)} old tags from qBittorrent...")
        client.torrents_delete_tags(tags=empty_tags)
        logger.info(f"Done removing {len(empty_tags)} old tags from qBittorrent")

    unique_hashes = set()
    for hash_list in tag_hashes.values():
        unique_hashes.update(hash_list)

    # Apply tags
    for tag in tag_hashes:
        if args.size:
            size = qbtools.utils.format_bytes(tag_sizes[tag])
            client.torrents_add_tags(
                tags=f"{tag} [{size}]", torrent_hashes=tag_hashes[tag]
            )
        else:
            client.torrents_add_tags(tags=tag, torrent_hashes=tag_hashes[tag])

    logger.info(
        f"Completed tagging {len(unique_hashes)} torrents with {len(tag_hashes)} tags"
    )


def add_arguments(subparser):
    """
    Description:
        Tag torrents. This command can be used to tag torrents with various tags, such as torrents that have not been active for a while, torrents that have not been working for a while, torrents that have expired an ratio or seeding time, torrents that have the same content path, etc.
    Usage:
        qbtools.py tagging --help
    Example:
        # Tag torrents
        qbtools.py tagging --exclude-category manual --added-on --expired --last-activity --sites --unregistered
    """
    parser = subparser.add_parser("tagging")
    parser.add_argument(
        "--exclude-category",
        nargs="*",
        action="append",
        metavar="mycategory",
        default=[],
        help="Exclude all torrent with this category, can be repeated multiple times",
        required=False,
    )
    parser.add_argument(
        "--exclude-tag",
        nargs="*",
        action="append",
        metavar="mytag",
        default=[],
        help="Exclude all torrents with this tag, can be repeated multiple times",
        required=False,
    )
    parser.add_argument(
        "--added-on",
        action="store_true",
        help="Tag torrents with added date (last 24h, 7 days, 30 days, etc)",
    )
    parser.add_argument(
        "--domains", action="store_true", help="Tag torrents with tracker domains"
    )
    parser.add_argument(
        "--duplicates",
        action="store_true",
        help="Tag torrents with the same content path",
    )
    parser.add_argument(
        "--expired",
        action="store_true",
        help="Tag torrents that have expired an ratio or seeding time, use with filtering by category/tag",
    )
    parser.add_argument(
        "--last-activity",
        action="store_true",
        help="Tag torrents with last activity date (last 24h, 7 days, 30 days, etc)",
    )
    parser.add_argument(
        "--not-linked",
        action="store_true",
        help="Tag torrents with files without hardlinks or symlinks, use with filtering by category/tag",
    )
    parser.add_argument(
        "--not-working",
        action="store_true",
        help="Tag torrents with not working tracker status",
    )
    parser.add_argument(
        "--sites", action="store_true", help="Tag torrents with known site names"
    )
    parser.add_argument(
        "--size",
        action="store_true",
        help="Add size of tagged torrents to created tags",
    )
    parser.add_argument(
        "--tracker-down",
        action="store_true",
        help="Tag torrents with temporarily down trackers",
    )
    parser.add_argument(
        "--unregistered",
        action="store_true",
        help="Tag torrents with unregistered tracker status message",
    )
    qbtools.add_default_args(parser)
