import argparse
import os
import pathlib


def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0: "B", 1: "KiB", 2: "MiB", 3: "GiB", 4: "TiB"}
    while size > power:
        size /= power
        n += 1
    formatted = round(size, 2)
    return f"{formatted} {power_labels[n]}"


def seconds(days: int) -> int:
    seconds_in_a_day = 86400
    seconds = days * seconds_in_a_day
    return seconds


def days(seconds: int) -> int:
    seconds_in_a_day = 86400
    days = seconds / seconds_in_a_day
    return days


def dhms(total_seconds: int) -> str:
    seconds = total_seconds % 60
    total_minutes = total_seconds // 60
    total_hours = total_minutes // 60
    minutes = total_minutes % 60
    days = total_hours // 24
    hours = total_hours % 24
    return f"{days}d{hours}h{minutes}m{seconds}s"


def is_linked(path):
    path = pathlib.Path(path)
    if os.path.islink(path):
        return True
    if os.path.isfile(path) and os.lstat(path).st_nlink > 1:
        return True
    if os.path.isdir(path):
        linked = [os.path.join(path, x) for path, subdirs, files in os.walk(path) for x in files if os.lstat(os.path.join(path, x)).st_nlink > 1 or os.path.islink(os.path.join(path, x))]
        return len(linked) > 0


class EnvDefault(argparse.Action):
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
