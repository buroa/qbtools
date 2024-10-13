import os
import shutil

from fnmatch import fnmatch


def __init__(app, logger):
    logger.info("Checking for orphaned files on disk not in qBittorrent...")

    completed_dir = app.client.application.preferences.save_path
    categories = [
        os.path.join(completed_dir, category.savePath)
        for (_, category) in app.client.torrent_categories.categories.items()
    ]
    exclude_patterns = [i for s in app.exclude_pattern for i in s]

    def get_size(path):
        """Calculate the size of a file or directory."""
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            total = 0
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total += os.path.getsize(fp)
            return total
        return 0

    def delete(item_path):
        if app.dry_run:
            logger.info(f"Skipping ...{os.path.relpath(item_path, start=completed_dir)} because --dry-run was specified")
            return

        try:
            item_size = get_size(item_path)  # Get the size of the item before deletion

            if os.path.isfile(item_path):
                os.remove(item_path)
                logger.info(f"Deleted ...{os.path.relpath(item_path, start=completed_dir)}")
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                logger.info(f"Deleted ...{os.path.relpath(item_path, start=completed_dir)}")
            else:
                logger.debug(f"{os.path.relpath(item_path, start=completed_dir)} does not exist")
                return

            return item_size
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    def cleanup_dir(folder_path, owned_files):
        """
        Clean up files and folders within `folder_path` that are not owned by qbittorrent
        :param folder_path: parent folder where we are cleaning up
        :param owned_files: files and folders that should not be deleted
        :return:
        """
        total_size_deleted = 0

        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if item_path in owned_files:
                continue
            if any(
                fnmatch(item, pattern) or fnmatch(item_path, pattern)
                for pattern in exclude_patterns
            ):
                logger.info(
                    f"Skipping {item_path} because it matches an exclude pattern"
                )
                continue

            deleted_size = 0

            if os.path.isfile(item_path):
                deleted_size = delete(item_path)
            elif os.path.isdir(item_path):
                owned_subfiles = set(
                    filter(lambda x: x.startswith(item_path), owned_files)
                )
                if not owned_subfiles and item_path not in categories:
                    deleted_size = delete(item_path)
                else:
                    deleted_size = cleanup_dir(item_path, owned_subfiles)

            if deleted_size:
                total_size_deleted = total_size_deleted + deleted_size

        return total_size_deleted

    # Gather list of all paths owned by qBittorrent
    qbittorrent_items = set()
    for torrent in app.client.torrents.info():
        # arbitrary cut-off to prevent traversing excessively large torrents
        if len(torrent.files) > 100:
            qbittorrent_items.add(torrent.content_path)
        else:
            qbittorrent_items.update(
                [os.path.join(torrent.save_path, file.name) for file in torrent.files]
            )

    # Delete orphaned files on disk not owned by qBittorrent
    total_size_deleted = cleanup_dir(completed_dir, qbittorrent_items)

    # Log the total size deleted
    logger.info(f"Total size deleted: {total_size_deleted / (1024 * 1024 * 1024):.2f} GB")


def add_arguments(command, subparser):
    """
    Description:
        Search for files on disk that are not in qBittorrent and delete them. Pair this with the prune command to delete torrents that are not in qBittorrent.
    Usage:
        qbtools.py orphaned --help
    Example:
        # Delete all files in the completed directory that are not in qBittorrent and don't match the exclude patterns
        qbtools.py orphaned --exclude-pattern "*_unpackerred" --exclude-pattern "*/manual/*" --dry-run
    """
    parser = subparser.add_parser(command)
    parser.add_argument(
        "--exclude-pattern",
        nargs="*",
        action="append",
        metavar="mypattern",
        default=[],
        help="Exclude pattern, can be repeated multiple times",
        required=False,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not delete any data on disk",
        default=False,
        required=False,
    )
