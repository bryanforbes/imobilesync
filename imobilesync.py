#! /usr/bin/env python

from optparse import OptionParser
import sys

def main():
    parser = OptionParser("Usage: %prog --[sync_type] args")
    parser.add_option('--contacts', action='append_const', dest='sync_type', const='Contacts')
    parser.add_option('--calendars', action='append_const', dest='sync_type', const='Calendars')

    (options, args) = parser.parse_args()

    if options.sync_type is None:
        print "ERROR: You must specify at least one sync type."
        parser.print_usage()
        sys.exit(1)

if __name__ == '__main__':
    main()
