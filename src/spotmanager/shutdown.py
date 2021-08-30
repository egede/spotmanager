#!/usr/bin/env python
import logging
import argparse
import socket
import subprocess

from logging.handlers import RotatingFileHandler
from datetime import datetime

from spotmanager.slackhandler import SlackChannelHandler

condorstatus = {1: 'Idle',
                2: 'Running',
                3: 'Removing',
                4: 'Completed',
                5: 'Held',
                6: 'Transferring Output',
                7: 'Suspended'}

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
        sf = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        sh.setFormatter(sf)
        logger.addHandler(sh)
    
    logger.debug('Starting')

    host = socket.gethostname()
    ip = socket.gethostbyname(host)
    ret = subprocess.run('uptime', stdout=subprocess.PIPE)
    uptime = ret.stdout.decode('utf-8')[10:]
    message = f'The machine {host} with IP {ip} is shutting down: {uptime}.'

    logger.info(message)
    
    logger.debug('Stopping')

if __name__ == '__main__':
    main()
