#!/usr/bin/python

import os
import os.path
import glob
import sys
import logging
from datetime import datetime
from datetime import timedelta

logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s [%(asctime)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
        )

DATE = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
DEFAULT_SAVE_DIR = '/home/test/RADIUS'


def combile_files(filename_iter, out_dir):
    src_file = None
    target_filename = os.path.join(out_dir, 'radius.log_%s' % DATE)
    logging.info('Merging all radius log files to %s' % target_filename)
    target_file = open(target_filename, 'w')
    try:
        for filename in filename_iter:
            src_file = open(filename)
            target_file.writelines(src_file)
            src_file.close()
            target_file.write('\n')
            os.remove(filename)
    finally:
        target_file.close()


def target_file_iterator(src_dirs):
    for d in src_dirs:
        target_files = glob.glob(os.path.join(d, 'radius.log_%s*' % DATE))
        if not target_files:
            continue
        logging.info('files matched: %s', repr(target_files))
        for filename in filter(lambda f : os.path.isfile(f), target_files):
            yield filename



def main():
    if len(sys.argv) < 2:
        print >> sys.stderr, "Usage: %s dir_list_file [output_dir]" % sys.argv[0]
        sys.exit(1)
    dirs = open(sys.argv[1]).readlines()
    dirs = [ d.strip() for d in dirs if not d.isspace()]
    out_dir = DEFAULT_SAVE_DIR
    if len(sys.argv) >= 3:
        out_dir = sys.argv[2]
    combile_files(target_file_iterator(dirs), out_dir)

if __name__ == '__main__':
    main()

