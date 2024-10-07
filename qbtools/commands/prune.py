from qbtools import utils
from fnmatch import fnmatch


def __init__(app, logger):
    categories = list(app.client.torrent_categories.categories.keys())

    if app.include_category:
        includes = [i for s in app.include_category for i in s]
        categories = list(
            filter(lambda c: any(fnmatch(c, p) for p in includes), categories)
        )

    if app.exclude_category:
        excludes = [i for s in app.exclude_category for i in s]
        categories = list(
            filter(lambda c: not any(fnmatch(c, p) for p in excludes), categories)
        )

    if not categories:
        logger.info(
            f"No torrents can be pruned since no categories were included based on selectors"
        )

    torrents = app.client.torrents.info()
    torrents = list(
        filter(lambda x: x.category in categories, torrents)
    )

    include_tags = [i for s in app.include_tag for i in s]
    if include_tags:
        torrents = list(
            filter(lambda x: all(y in x.tags for y in include_tags), torrents)
        )
    exclude_tags = [i for s in app.exclude_tag for i in s]
    if exclude_tags:
        torrents = list(
            filter(
                lambda x: not any(y in x.tags for y in exclude_tags), torrents
            )
        )

    logger.info(
        f"Pruning torrents with tags [{' AND '.join(include_tags)}] but does not contain tags [{' OR '.join(exclude_tags)}]..."
    )

    for t in torrents:
        logger.info(
            f"Pruned torrent {t['name']} with category [{t.category}] and tags [{t.tags}] and ratio [{round(t['ratio'], 2)}] and seeding time [{utils.dhms(t['seeding_time'])}]"
        )
        if not app.dry_run:
            t.delete(delete_files=app.with_data)

    logger.info(f"Deleted {len(torrents)} torrents")


def add_arguments(command, subparser):
    """
    Description:
        Prune torrents that have matching tags. Pair this with the tagging command to tag torrents.
    Usage:
        qbtools.py prune --help
    Example:
        # Delete torrents with the tag 'expired' and 'added:30d', however if the torrent also has the tags 'site:oink' or 'site:whatcd' exclude it from being deleted
        qbtools.py prune --include-tag expired --include-tag added:30d --exclude-tag site:oink --exclude-tag site:whatcd --dry-run
    """
    parser = subparser.add_parser(command)
    parser.add_argument(
        "--include-tag",
        nargs="*",
        action="append",
        metavar="mytag",
        default=[],
        help="Include torrents containing all of these tags, can be repeated multiple times",
        required=True,
    )
    parser.add_argument(
        "--exclude-tag",
        nargs="*",
        action="append",
        metavar="mytag",
        default=[],
        help="Exclude torrents containing any of these tags, can be repeated multiple times",
        required=False,
    )
    parser.add_argument(
        "--include-category",
        nargs="*",
        action="append",
        metavar="mycategory",
        default=[],
        help="Include torrents only from category that matches this pattern, can be repeated multiple times. If not specified, all categories are included",
        required=False,
    )
    parser.add_argument(
        "--exclude-category",
        nargs="*",
        action="append",
        metavar="mycategory",
        default=[],
        help="Exclude torrents from category that matches this pattern, can be repeated multiple times",
        required=False,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not delete torrents",
        default=False,
        required=False,
    )
    parser.add_argument(
        "--with-data",
        action="store_true",
        help="Delete torrents with data",
        default=False,
        required=False,
    )
