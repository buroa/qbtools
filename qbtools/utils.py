def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0: "B", 1: "KiB", 2: "MiB", 3: "GiB", 4: "TiB"}
    while size > power:
        size /= power
        n += 1
    formatted = round(size, 2)
    return f"{formatted} {power_labels[n]}"


def filter_tracker_by_domain(domain, trackers=[]):
    for tracker in trackers:
        if any(domain in url for url in tracker["urls"]):
            return tracker


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
