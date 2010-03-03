import sys

import imobiledevice, datetime
from imobilesync.options import parser
from imobilesync.sync import Sync, SyncError
from imobilesync.data import *
from imobilesync.config import state

def main():
    (options, args) = parser.parse_args()

    if options.sync_type is None:
        print "ERROR: You must specify at least one sync type."
        parser.print_usage()
        sys.exit(1)

    try:
        s = Sync()
        s.connect()

        try:
            for sync_type in options.sync_type:
                if not sync_type.state.last_sync_time or options.ignore_sync_time:
                    print s.serialize_all(sync_type)
                else:
                    print s.serialize_changed(sync_type)

                s.finish(sync_type, not options.ignore_sync_time)
        except SyncError, e:
            print 'An error was encountered: %s' % e
        finally:
            s.disconnect()
    except SyncError, e:
        print 'An error was encountered: %s' % e

    state.write()
