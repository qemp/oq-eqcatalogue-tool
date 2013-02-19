#!/usr/bin/env python

import sys
import os
import argparse

from eqcatalogue import CatalogueDatabase
from eqcatalogue.importers import V1, Iaspei, store_events

fmt_map = {'isf': V1, 'iaspei': Iaspei}


def build_cmd_parser():
    """Create a parser for cmdline arguments"""

    parser = argparse.ArgumentParser(prog='LoadCatalogueDB')

    parser.add_argument('-i', '--input-file',
                        nargs=1,
                        type=str,
                        metavar='input catalogue file',
                        dest='input_file',
                        help=('Specify the input file containing earthquake'
                                'events supported formats are ISF and IASPEI'))

    parser.add_argument('-f', '--format-type',
                        nargs=1,
                        type=str,
                        help=('Specify the earthquake catalogue format,'
                              'valid formats are: isf, iaspei'),
                        metavar='format type',
                        dest='format_type')

    parser.add_argument('-db', '--db-name',
                        nargs=1,
                        type=str,
                        default='eqcatalogue.db',
                        help='Specify db filename',
                        metavar='db filename',
                        dest='db_filename')
    return parser


def check_args(args):
    input_file = args.input_file[0]
    fmt_file = args.format_type[0]
    filename = (os.path.abspath(input_file)
            if os.path.exists(input_file) else None)
    cat_format = (fmt_file.lower()
            if fmt_file.lower() in ['isf', 'iaspei']
            else None)
    if filename is None:
        print 'Can\'t find the provided input file'
        sys.exit(-1)
    if cat_format is None:
        print 'Format %s is not supported' % fmt_file
        sys.exit(-1)
    return filename, cat_format


if __name__ == '__main__':
    parser = build_cmd_parser()
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        args = parser.parse_args()
        filename, cat_format = check_args(args)
        cat_dbname = (args.db_filename[0] if isinstance(args.db_filename, list)
                      else args.db_filename)
        with open(filename, 'r') as cat_file:
            cat_db = CatalogueDatabase(filename=cat_dbname)
            store_events(fmt_map[cat_format], cat_file, cat_db)
        sys.exit(0)
