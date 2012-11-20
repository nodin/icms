#!/usr/bin/python

import itertools
import os.path
import sys
import shutil
import logging
import logging.handlers
from datetime import datetime
from datetime import timedelta
from logger import log

DATE = (datetime.now() - timedelta(days=1))

def _config_logging(level=logging.INFO):
    """logging configuration"""
    logfile = '/var/log/radius_parser.log'

    # Only configure the root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=20480000, backupCount=5)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def _any(func, it):
    for item in it:
        if func(item): return True
    return False


def _partition(s, sep):
    pos = s.find(sep)
    if pos < 0:
        return (s, '', '')
    return (s[:pos], sep, s[pos+1:])


def _extract_nvpair(data):
    fields = _partition(data, '=')[::2]
    key = fields[0].strip().lower()
    val = fields[1].strip()
    if not key:
        return (None, None)
    if val and val[0] == '"' and val[-1] == '"':
        val = val[1:-1]
    return (key, val)


def _hexstr2int(data):
    return tuple([int(data[i*2:i*2+2], 16) for i in range(len(data) / 2)])


def _decode_str(digits):
    return ''.join([chr(d) for d in digits])


def _nssp(node, shelf, slot, port):
    node = node.replace('-', '').replace('_', '')
    result = '%s_%s/%s/%s' % (node, shelf, slot.rjust(2, '0'), port.rjust(2, '0'))
    return result.upper()


def _parse_cid(cid):
    node, other = cid.strip().split()
    slot_port, _, other = _partition(other, ':')
    slot, _, port = _partition(slot_port, '/')
    return node, slot, port


class RadiusRecord(object):
    def __init__(self, mac, remote_id, cid=None):
        self.mac = mac
        self.remote_id = remote_id
        self.cid = cid

    def __repr__(self):
        return "[mac:%s, remote-id:%s, circuit-id:%s]" % (self.mac, self.remote_id, self.cid)


VALID_MAC_PREFIXES = ("0019CB", "0002CF", "0023F8", "404A03", "001349", "5067F0", "C86C87", "CC5D4E")

def build_radius_record(recdict):
    cid = 'circuit-id-tag' in recdict and recdict['circuit-id-tag'] or ''
    mac = recdict.get('mac', '').upper()
    if not mac:
        return None
    if _any(lambda x : mac.startswith(x), VALID_MAC_PREFIXES):
        mac = ':'.join([mac[i*2 : (i+1)*2] for i in range(len(mac) / 2)])
        return RadiusRecord(mac, recdict['remote-id-tag'], cid=cid)
    else:
        log.info("Non-ZyXel device found, MAC: " + mac)
        return None

def rad_recv_record_extractor(input_iter):
    recdict = None
    for line in input_iter:
        if line[0].isspace():
            if not recdict:
                recdict = {}
            key, val = _extract_nvpair(line)
            if not key or not val:
                continue
            if key.lower() == 'calling-station-id':
                recdict['mac'] = val.replace('.', '')
            elif key.lower() == 'cisco-avpair':
                ckey, cval = _extract_nvpair(val)
                if ckey:
                    recdict[ckey] = cval
        elif recdict:
            record = build_radius_record(recdict)
            if record: yield record
            recdict = None
    if recdict:
        record = build_radius_record(recdict)
        if record: yield record


NOKIA_SHELF = '1'
ECI_SHELF = '1'
HUAWEI_SHELF = '0'
SIEMENS_PORT = '17'


def utstarcom_converter(rad):
    digits = _hexstr2int(rad.remote_id)
    node = _decode_str(digits[18:28])
    shelf, slot, port = tuple([x + 1 for x in digits[28:31]])
    return rad.mac, _nssp(node, str(shelf), str(slot), str(port))


def huawei_converter(rad):
    normalized_cid = rad.remote_id.replace('0002 GE', '').replace('-IPM', '').replace('atm', '')
    node, slot, port = _parse_cid(normalized_cid)
    return rad.mac, _nssp(node, HUAWEI_SHELF, slot, port)


def nokia_converter(rad):
    node, slot, port = _parse_cid(rad.cid)
    return rad.mac, _nssp(node, NOKIA_SHELF, slot, port)


def eci_converter(rad):
    normalized_cid = rad.remote_id.replace('atm', '')
    node, slot, port = _parse_cid(normalized_cid)
    return rad.mac, _nssp(node, ECI_SHELF, slot, port)


def siemens_converter(rad):
    normalized_cid = rad.remote_id.replace('-', ' ', 1).replace('-', ':', 1)
    node, shelf, slot = _parse_cid(normalized_cid)
    return rad.mac, _nssp(node, shelf, slot, SIEMENS_PORT)


CONVERTER_CHAIN = (
        (utstarcom_converter,   lambda x : x.remote_id.startswith('0000079d')),
        (nokia_converter,       lambda x : x.remote_id.startswith('030200000000')),
        (huawei_converter,      lambda x : 'HUAG' in x.remote_id),
        (siemens_converter,     lambda x : 'SIIP' in x.remote_id),
        # Make sure ECI rule is at last since HUAWEI cids may also contain 'atm'
        (eci_converter,         lambda x : 'atm' in x.remote_id),
    )


DEFAULT_RADIUS_LOG_DIR = '/var/log/'
HISTORY_DIR = 'History_RADIUS'

def parse_radius_log(radius_log_file, out_dir):
    log_file = open(radius_log_file, 'r')
    outfile_name = "RADIUS_MAC2NSP_%s.txt" % (DATE.strftime('%Y%m%d'))
    output_file = open(os.path.join(out_dir, outfile_name), 'w')
    existing = set()
    try:
        for record in rad_recv_record_extractor(log_file):
            for converter_func, check_func in CONVERTER_CHAIN:
                if check_func(record):
                    try:
                        mac, nssp = converter_func(record)
                    except Exception, e:
                        #logging.error("Error passing radius record: " + repr(e))
                        log.exception('Error parsing radius record')
                        continue
                    mac2nsp = "%s %s" % (mac, nssp)
                    if mac2nsp in existing:
                        log.warn("Duplicate record found: %s, ignoring..." % mac2nsp)
                    else:
                        log.info("Matched: %s %s" % (mac, nssp))
                        output_file.write("%s %s\n" % (mac, nssp))
                        existing.add(mac2nsp)
                    break
            else:
                log.info("Radius record not matching rule: " + repr(record))
    finally:
        log_file.close()
        output_file.close()


def get_radius_log_path(log_dir):
    log_filename = "radius.log_%s" % DATE.strftime('%Y%m%d')
    return os.path.join(log_dir, log_filename)


def move_parsed_file(filename, out_dir):
    hist_dir = os.path.join(out_dir, HISTORY_DIR)
    if not os.path.exists(hist_dir):
        os.mkdir(hist_dir)
    log.info("Moving %s to %s" % (filename, hist_dir))
    shutil.move(filename, hist_dir)

def parseRadius():
    log_dir = "/tmp/"
    log_path = get_radius_log_path(log_dir)
    log.info("Parsing log file %s" % log_path)
    try:
        parse_radius_log(log_path, DEFAULT_RADIUS_LOG_DIR)
        move_parsed_file(log_path, DEFAULT_RADIUS_LOG_DIR)
    except:
        pass

def main():
    log_dir = DEFAULT_RADIUS_LOG_DIR
    if len(sys.argv) > 1:
        log_dir = sys.argv[1]
    log_path = get_radius_log_path(log_dir)
    logging.info("Parsing log file %s" % log_path)
    try:
        parse_radius_log(log_path, log_dir)
        move_parsed_file(log_path, log_dir)
    except:
        logging.exception('Error parsing radius log')


if __name__ == '__main__':
    _config_logging()
    main()
