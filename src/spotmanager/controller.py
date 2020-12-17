#!/usr/bin/env python
import logging
import argparse

from logging.handlers import RotatingFileHandler

from spotmanager.manager import manager

def main():

    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    ap = argparse.ArgumentParser(description='Manage spot instances on Nectar')
    ap.add_argument("-v", "--verbose", action="count",
                    help="Increase verbosity by enabling DEBUG in the logger.")
    ap.add_argument("-s", "--stdout", action="count",
                    help="Perform logging to stdout instead of a file")
    ap.add_argument("-l", "--logfile", default="spotmanager.log",
                    help="File to write logging information to.")
    ap.add_argument("-n", "--number-hosts", type=int, default=25,
                    help="The maximum number of hosts to have at the same time.")
    ap.add_argument("-c", "--configfile", default='ppoc-1-openrc.sh',
                    help="The files that contains the .rc file for access to Nectar.")
    ap.add_argument("-k", "--keyfile", default='~/.ssh/id_rsa',
                    help="Private key to use for authentication to instances.")

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

    
    logger.info('Starting')
    logger.debug('Verbose mode is enabled.')
    m = manager(args.configfile, args.keyfile)
    m.event(maxhost=args.number_hosts)
    logger.info('Stopping')

if __name__ == '__main__':
    main()
