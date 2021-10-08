import os, time

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
