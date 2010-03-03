from optparse import OptionParser

parser = OptionParser("Usage: %prog --[sync_type] args")
parser.add_option('-i', '--ignore-sync-time', action='store_true', dest='ignore_sync_time', default=False)

from imobilesync.data import *
