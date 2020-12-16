#!/usr/bin/env python
import logging

from logging.handlers import RotatingFileHandler

from spotmanager.manager import manager

def main():

    # create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fh = RotatingFileHandler('spotmanager.log', maxBytes=1000000, backupCount=5)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    
    logger.info('Starting')
    m = manager()
    m.event()
    logger.info('Stopping')

if __name__ == '__main__':
    main()
