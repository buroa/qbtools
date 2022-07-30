import os, time, stat
import pathlib3x as pathlib

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : 'B', 1: 'KiB', 2: 'MiB', 3: 'GiB', 4: 'TiB'}
    while size > power:
        size /= power
        n += 1
    formatted = round(size, 2)
    return f"{formatted} {power_labels[n]}"

def free_space(path):
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize

def iowait(interval):
    tick = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
    numcpu = os.cpu_count()
    readstats = open('/proc/stat')
    procstats = readstats.readlines()[0].split()
    user, nice, sys, idle, iowait, irq, sirq = ( float(procstats[1]), float(procstats[2]),
                                            float(procstats[3]), float(procstats[4]),
                                            float(procstats[5]), float(procstats[6]),
                                            float(procstats[7]) )
    readstats.close()
    time.sleep(interval)
    readstats = open('/proc/stat')
    procstats = readstats.readlines()[0].split()
    userd, niced, sysd, idled, iowaitd, irqd, sirqd = ( float(procstats[1]), float(procstats[2]),
                                            float(procstats[3]), float(procstats[4]),
                                            float(procstats[5]), float(procstats[6]),
                                            float(procstats[7]) )
    readstats.close()
    iowait = '{0:.1f}'.format(((iowaitd - iowait)* 100 / tick ) / numcpu / interval)

    return float(iowait)

def is_linked(path):
    path = pathlib.Path(path)

    if os.path.islink(path):
        return True

    if os.path.isfile(path) and os.lstat(path).st_nlink > 1:
        return True

    if os.path.isdir(path):
        linked = [path / x for path, subdirs, files in os.walk(path) for x in files if os.lstat(path / x).st_nlink > 1]

        return len(linked) > 0