#!/usr/bin/python

import os.path
import ftplib
import sys
import logging
from datetime import datetime
from datetime import timedelta

logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s [%(asctime)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
        )

DATE = (datetime.now() - timedelta(days=1)).strftime("%m%d%y")
DEFAULT_SAVE_DIR = '/home/test/ICMS'
FILE_NAME_MAPPING = (
        ('MLD', 'MLD'),
        ('MLU', 'MLU'),
        ('MLR', 'MLR'),
        ('MLS', 'MLS'),
        ('BB_MLBD', 'MLD'),
        ('BB_MLBV', 'MLU'),
        ('BB_MLBR', 'MLR'),
        )


def process_file(ftp, filename, save_dir):
    for spref, tpref in FILE_NAME_MAPPING:
        if filename.startswith(spref + DATE):
            break
    else:
        logging.debug('Ignoring file %s' % filename)
        return
    f = open(os.path.join(save_dir, '%s%s.TXT' % (tpref, DATE)), 'a')
    try:
        ftp.retrlines('RETR ' + filename, lambda l : f.write(l + '\n'))
        f.flush()
    except:
        logging.exception('error downloading %s' % filename)
    finally:
        f.close()


def process_ftp_server(host, port, user, passwd, path, save_dir):
    ftp = ftplib.FTP()
    try:
        ftp.connect(host, int(port))
        ftp.login(user, passwd)
        if path:
            ftp.cwd(path)
        files = ftp.nlst()
        for filename in files:
            process_file(ftp, filename, save_dir)
    except:
        logging.exception('error downloading file')
    finally:
        ftp.close()


def main():
    if len(sys.argv) < 2:
        print >> sys.stderr, 'Usage: %s config_file' % sys.argv[0]
        sys.exit(1)
    config = _read_properties(sys.argv[1])
    host = config.get('host', None)
    port = config.get('port', '21')
    user = config.get('username', None)
    pwd  = config.get('password', None)
    if not host or not port or not user or not pwd:
        print >> sys.stderr, 'FTP config incomplete. Must include host, port, username and password.'
        sys.exit(2)
    path = config.get('path', None)
    save_dir = config.get('save.dir', DEFAULT_SAVE_DIR)
    process_ftp_server(host, port, user, pwd, path, save_dir)


def _read_properties(filepath):
    """Read a properties file and return a dict containing the key-values"""
    result = {}
    f = open(filepath)
    try:
        for line in f:
            line = line.strip()
            if line[0:1] == '#':
                continue
            pos = line.find('=')
            if pos > 0:
                if pos < len(line):
                    result[line[0:pos].strip()] = line[pos+1:].strip()
                else:
                    result[line[0:pos].strip()] = ""
    finally:
        f.close()
    return result

if __name__ == '__main__':
    main()
