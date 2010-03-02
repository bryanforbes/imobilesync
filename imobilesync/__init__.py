from optparse import OptionParser
import sys, pdb

import imobiledevice, datetime
from imobilesync.sync import Sync
from imobilesync.data import Contacts, Calendars
from imobilesync.config import state

def main():
    parser = OptionParser("Usage: %prog --[sync_type] args")
    parser.add_option('--contacts', action='append_const', dest='sync_type', const=Contacts)
    parser.add_option('--calendars', action='append_const', dest='sync_type', const=Calendars)
    parser.add_option('-i', '--ignore-sync-time', action='store_true', dest='ignore_sync_time', default=False)

    (options, args) = parser.parse_args()

    if options.sync_type is None:
        print "ERROR: You must specify at least one sync type."
        parser.print_usage()
        sys.exit(1)

    s = Sync()
    s.connect()

    for sync_type in options.sync_type:
        if not sync_type.state.last_sync_time or options.ignore_sync_time:
            print s.serialize_all(sync_type)
        else:
            print s.serialize_changed(sync_type)

        s.finish(sync_type, not options.ignore_sync_time)
    s.disconnect()

    state.write()

if __name__ == '__main__':
    main()
