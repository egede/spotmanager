#!/usr/bin/env python
import logging
import argparse

from collections import Counter
from logging.handlers import RotatingFileHandler
from datetime import datetime

import htcondor
from spotmanager.slackhandler import SlackChannelHandler

condorstatus = {1: 'Idle',
                2: 'Running',
                3: 'Removing',
                4: 'Completed',
                5: 'Held',
                6: 'Transferring Output',
                7: 'Suspended'}

def main():

    logger = logging.getLogger('Monitor')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    ap = argparse.ArgumentParser(description='Monitor health of machines and jobs')
    ap.add_argument("-v", "--verbose", action="count",
                    help="Increase verbosity by enabling DEBUG in the logger.")
    ap.add_argument("-s", "--stdout", action="count",
                    help="Perform logging to stdout instead of a file")
    ap.add_argument("-l", "--logfile", default="monitor.log",
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
    
    logger.debug('Verbose mode is enabled.')
    logger.debug('Starting')


    schedd = htcondor.Schedd()

    status = [ad['JobStatus'] for ad in
              schedd.query(constraint='true', projection=['JobStatus'])]
    message = '```\n'
    message += 'The following jobs are in processing:\n'
    for k,v in Counter(status).items():
        message += f'{condorstatus[k]:15}, {v:3}\n'
    message +='```'
    logger.info(message)
    
    now = int(datetime.now().timestamp())
    ndone = 0
    message = '```\n'
    message +=  'Status     Start             Stop              Host\n'
    message += '===================================================\n'
    for ad in schedd.history(constraint=f'CompletionDate > {now}-86400',
                             projection=['JobStatus',
                                         'JobStartDate',
                                         'CompletionDate',
                                         'LastRemoteHost'],
                             match=-1):
        ndone+=1
        start = datetime.fromtimestamp(ad['JobStartDate']).isoformat(' ')
        stop = datetime.fromtimestamp(ad['CompletionDate']).isoformat(' ')
        message+=f' {ad["JobStatus"]:4}   '
        message+=f'{start:19} '
        message+=f'{stop:19} '
        message+=f'{ad["LastRemoteHost"][4:-10]}\n'

    message +='```'
    summary = f'In the last 24h {ndone} jobs finished.'
    logger.info(summary)
    logger.debug(message)
    
    logger.debug('Stopping')

if __name__ == '__main__':
    main()
