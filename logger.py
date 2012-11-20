import logging
import os.path

#--- log config ----------------------------------------------

"""create log object"""
logging.basicConfig(
        filename='/var/log/icms_parser.log',
        level=logging.INFO,
        format='%(levelname)s [%(asctime)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
)

log=logging.getLogger('icms_parser')


