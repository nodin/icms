#!/usr/bin/python

import os
import os.path
import shutil
from ftplib import FTP
from datetime import datetime
from datetime import timedelta
from logger import log
from icms_parser import parse_subscriber
from icms_parser import subscriber_to_string
from icms_descriptors import DESCRIPTORS
from dhcp_parse import parseDHCPFile
from radius_parse import parseRadius


ICMS_HISTORY_DIR = 'History_ICMS'
DHCP_HISTORY_DIR = 'History_OPTION82'
RADIUS_HISTORY_DIR = 'History_RADIUS'

def main(onems_root_path):
    """Main flow"""
    general_prop = _read_properties(os.path.join(onems_root_path, 'conf', 'general.properties'))
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    target_dir = os.path.join(onems_root_path, 'ftproot', 'pldt')
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    try:
        ftp_conf_icms = _get_ftp_config(general_prop, 'icms')
        icms_file_path = os.path.join('/tmp', 'subscriber_%s.txt' % timestamp)
        invalid_file_dir = general_prop['icms.invalid.file.dir']
        if not invalid_file_dir:
            invalid_file_dir = '/var/log'
        save_icms_files(ftp_conf_icms, icms_file_path, invalid_file_dir)
        shutil.copy(icms_file_path, target_dir)
    except:
        log.exception("Error saving icms files")

    try:
        dhcp_names = set([ s.strip(' \r') for s in general_prop['dhcp.names'].strip(',').split(',') ])
    except:
        log.error("DHCP names not found, please check \"dhcp.names\" property in /OneMS/conf/general.properties.")
        return

    for dhcp_name in dhcp_names:
        if not dhcp_name:
            continue
        try:
            ftp_conf_dhcp = _get_ftp_config(general_prop, dhcp_name)
            ftp_conf_radius = _get_ftp_config(general_prop, 'radius')
            lease_file_path = os.path.join('/tmp','%s.leases' % dhcp_name)
            radius_file_path = os.path.join('/tmp','radius.log_%s' % (_yesterday().strftime('%Y%m%d')))
            download_dhcp_leases(ftp_conf_dhcp,lease_file_path)
            download_radius_log(ftp_conf_radius,radius_file_path)
            parseDHCPFile(dhcp_name)
            parseRadius()
            dhcp_file_path = os.path.join('/tmp', 'device_%s_%s.txt' % (timestamp, dhcp_name) )
            save_dhcp_files(dhcp_name, dhcp_file_path)
            shutil.copy(dhcp_file_path, target_dir)
            os.remove(lease_file_path)
            os.remove(radius_file_path)
        except:
            log.exception("Error getting MAC2NSP files from DHCP server: %s", dhcp_name)


def save_icms_files(ftp_config, local_file_path, invalid_file_dir):
    ftp = _init_ftp_config(ftp_config)
    file_list = ftp.nlst()
    yesterday_str = _yesterday().strftime("%m%d%y")
    bbdt_yeseterday_str = _yesterday().strftime("%m%d%Y")

    localfile = open(local_file_path, 'w')

    try:
        for file_name_key in DESCRIPTORS.keys():
            name_prefix = file_name_key.upper() + yesterday_str
            name_bbdt_prefix = file_name_key.upper() + bbdt_yeseterday_str
            for fileslis in file_list:
                log.debug("file name is : "+fileslis)
            target_files = [ f for f in file_list if f[0 : len(name_prefix)] == name_prefix or f[0 : len(name_bbdt_prefix)] ==  name_bbdt_prefix]
            invalid_file_path = os.path.join(invalid_file_dir, "%s_INVALID.TXT" % name_prefix)
            invalidfile = _lazy_open(invalid_file_path, 'a')
            line_callback = _wrap_parse_subscriber(DESCRIPTORS[file_name_key], localfile, invalidfile)

            try:
                for file_name in target_files:
                    log.debug("Download and processing file: " + file_name)
                    ftp.retrlines('RETR ' + file_name, line_callback)
                move_downloaded_files(ftp, ICMS_HISTORY_DIR, target_files)
            finally:
                invalidfile.close()
    finally:
        localfile.close()
        ftp.close()

def download_dhcp_leases(ftp_config, local_file_path):
    #save dhcpd.leases into /tmp/dhcp#.leases.
    ftp = _init_ftp_config(ftp_config)
    leases_file_name = "dhcpd.leases"
    localfile = open(local_file_path,'w')
    try:
        log.debug("Download file: " + leases_file_name)

        try:
            ftp.retrlines('RETR ' + leases_file_name, lambda line : localfile.write(line + '\n'))
        except:
            pass
    finally:
        localfile.close()
        ftp.close()

def download_radius_log(ftp_config, local_file_path):
    radius_log_filename = "radius.log_%s" % (_yesterday().strftime('%Y%m%d'))

    ftp = _init_ftp_config(ftp_config)
    localfile = open(local_file_path,'w')
    try:
        log.debug("Download file: " + radius_log_filename)
        try:
            ftp.retrlines('RETR ' + radius_log_filename, lambda line : localfile.write(line + '\n'))
        except:
            pass
    finally:
        localfile.close()
        ftp.close()




def save_dhcp_files(dhcp_name, local_file_path):
    localfile = open(local_file_path, 'w')
    OUT_DIR='/var/log/'
    yesterday_str = _yesterday().strftime("%Y%m%d")
    file_name = "MAC2NSP_%s_%s.txt" % (yesterday_str,dhcp_name)
    radius_file_name = "RADIUS_MAC2NSP_%s.txt" % (yesterday_str)
    file_path = os.path.join(OUT_DIR,file_name)
    radius_file_path = os.path.join(OUT_DIR,radius_file_name)
    try:
        try:
            file = open(file_path, "r")
            log.debug("copy file: " + file_path)
            localfile.writelines(file)
            localfile.write('\n')
        except :
            log.info("not find file."+file_path)
            pass
        try:
            radius_file = open(radius_file_path, "r")
            log.debug("copy file: "+radius_file_path)
            localfile.writelines(radius_file)
            localfile.write('\n')
        except :
            log.info("not find file."+radius_file_path)
            pass
    finally:
        localfile.close()
    try:
        history_option82_dir = os.path.join(out_dir, DHCP_HISTORY_DIR)
        if os.path.isdir(history_option82_dir):
            os.mkdir(history_option82_dir)
        shutil.move(file_path,history_option82_dir)
        history_radius_dir = os.path.join(out_dir, RADIUS_HISTORY_DIR)
        if os.path.isdir(history_radius_dir):
            os.mkdir(history_radius_dir)
        shutil.move(radius_file_path,history_radius_dir)
        log.debug("move parse middle files to history.")
    except:
        pass # Ignore


def move_downloaded_files(ftp, directory, files):
    try:
        ftp.mkd(directory)
    except:
        pass # Ignore
    try:
        for f in files:
            ftp.rename(f, '%s/%s' % (directory, f))
    except:
        log.exception("Error moving files %s to history dir %s" % (repr(files), directory))



def _wrap_parse_subscriber(fieldDesc, localfile, invalidfile):
    # Callback function for ftp.retrlines
    def __parse_subscriber(line):
        subscriber = parse_subscriber(line, fieldDesc)
        if subscriber:
            localfile.write(subscriber_to_string(subscriber))
        else:
            log.info("Writting invalid record")
            invalidfile.write(line + '\n')
    return __parse_subscriber


def _yesterday():
    """Get yesterday"""
    return datetime.now() - timedelta(days=1)


def _init_ftp_config(config_dict):
    """create and initialize a FTP connection, and return the FTP object"""
    ftp = FTP()
    ftp.connect(config_dict['host'], int(config_dict['port']))
    ftp.login(config_dict['username'], config_dict['password'])
    if 'path' in config_dict:
        ftp.cwd(config_dict['path'])
    return ftp


def _read_properties(filepath):
    """Read a properties file and return a dict containing the key-values"""
    result = {}
    for line in open(filepath):
        line = line.strip()
        if line[0:1] == '#':
            continue
        pos = line.find('=')
        if pos > 0:
            if pos < len(line):
                result[line[0:pos].strip()] = line[pos+1:].strip()
            else:
                result[line[0:pos].strip()] = ""
    return result


def _get_ftp_config(confdict, keyprefix):
    result = {}
    result['host'] = confdict[keyprefix + ".ftp.address"]
    result['port'] = confdict[keyprefix + ".ftp.port"]
    result['username'] = confdict[keyprefix + ".ftp.username"]
    result['password'] = confdict[keyprefix + ".ftp.password"]
    result['path'] = confdict[keyprefix + ".ftp.path"]
    log.debug("FTP config for %s: %s" % (keyprefix, repr(result)) )
    return result


def _lazy_open(path, mode):
    # -------- Proxy class -------------------
    """Return a proxy for file object that opens file lazily"""
    class _LazyFileProxy(object):
        def __init__(self, path, mode):
            self.path = path
            self.mode = mode
            self.f = None

        def write(self, s):
            if not self.f:
                self.f = open(self.path, self.mode)
            self.f.write(s)

        def close(self):
            if self.f:
                self.f.close()
    # ---- END: Proxy class -------------------
    return _LazyFileProxy(path, mode)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print 'Usage: %s  onems_root_path' % sys.argv[0]
        sys.exit(1)

    onems_root_path = sys.argv[1]
    main(onems_root_path)
