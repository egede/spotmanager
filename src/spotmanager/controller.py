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
    ap.add_argument("-c", "--configfile", default='lhcb-simulation-openrc.sh',
                    help="The files that contains the .rc file for access to Nectar.")
    ap.add_argument("-k", "--keyfile", default='~/.ssh/id_rsa',
                    help="Private key to use for authentication to instances.")
    ap.add_argument("-l", "--logfile", default="spotmanager.log",
                    help="File to write logging information to.")
    ap.add_argument("-f", "--flavour", default="p3.medium",
                    help="Instance flavour to use when launching spot instances.")
    ap.add_argument("-n", "--number-hosts", type=int, default=25,
                    help="The maximum number of instances to have at the same time.")
    ap.add_argument("-r", "--remove", action="count",
                    help="Delete idle preemtible instances. Usually this option should be given but as it is dangerous it is not the default.")
    ap.add_argument("-s", "--stdout", action="count",
                    help="Perform logging to stdout instead of a file")
    ap.add_argument("-t", "--throttle", type=int, default=4,
                    help="The maximum new instances to start at a given time. If negative, no limit.")
    ap.add_argument("-z", "--zone", default='',
                    help="Zone to start instances in.")
    ap.add_argument("-S", "--sleepfactor", type=int, default=1,
                    help="How long to wait for actions to take place.")

    args = ap.parse_args()

    remove_instances = False
    if args.remove:
        remove_instances = True
    
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
    m.event(maxhosts=args.number_hosts, sleepfactor=args.sleepfactor, remove=remove_instances, throttle=args.throttle, zone=args.zone, flavour=args.flavour)
    logger.info('Stopping')

if __name__ == '__main__':
    main()
