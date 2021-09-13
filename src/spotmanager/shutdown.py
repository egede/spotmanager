#!/usr/bin/env python
import logging
import argparse
import socket
import fcntl
import struct
import os
import re

import subprocess

from logging.handlers import RotatingFileHandler
from datetime import datetime

from spotmanager.slackhandler import SlackChannelHandler


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
    return ip

def main():

    logger = logging.getLogger('Shutdown')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    ap = argparse.ArgumentParser(description='Log when machine is shut down')
    ap.add_argument("-v", "--verbose", action="count",
                    help="Increase verbosity by enabling DEBUG in the logger.")
    ap.add_argument("-s", "--stdout", action="count",
                    help="Perform logging to stdout instead of a file")
    ap.add_argument("-l", "--logfile", default="shutdown.log",
                    help="File to write logging information to.")
    ap.add_argument("-t", "--tokenfile", default='',
                    help="The file that contains the authentication for slack. If not given, there will be no logging to Slack")
    ap.add_argument("-c", "--channel", default='C02BATY8P4M',
                    help="The Slack channel")

    args = ap.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if args.stdout:
        lh = logging.StreamHandler()
        lh.setFormatter(formatter)
        logger.addHandler(lh)
    else:
        fname = args.logfile
        fh = RotatingFileHandler(fname, maxBytes=1000000, backupCount=5)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if len(args.tokenfile)>0:
        with open(args.tokenfile) as f:
            tk = f.readline().strip()

        sh = SlackChannelHandler(tk, args.channel)
        sf = logging.Formatter('%(name)s - %(message)s')
        sh.setFormatter(sf)
        logger.addHandler(sh)
    
    logger.debug('Starting')

    host = socket.gethostname()
    host = host.split('.')[0]
    network = bytes(os.listdir('/sys/class/net/')[0], 'utf-8')
    ip = get_ip_address(network)
    ret = subprocess.run('uptime', stdout=subprocess.PIPE)
    uptime = ret.stdout.decode('utf-8')[10:]
    short = re.search(r'^up\s+([0-9])\s+min', uptime) # Will match 9 minutes or less
    if not short:
        message = f'{host}:{ip} shutting down: {uptime}.'

        logger.info(message)
    
    logger.debug('Stopping')

if __name__ == '__main__':
    main()
