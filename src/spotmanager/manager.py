"""Manange instances in an openstack cloud"""
import datetime
import time
import uuid
import logging

from spotmanager.openstack import openstack
from spotmanager.instance import instance

logger = logging.getLogger(__name__)

class manager():
    """The manager class will through its event method query for the existence of running instances,
    retire from the condor queue servers that have been alive for a while (to prevent jobs running when 
    machines are pulled down), will pull down idle machines and finally create new ones."""
    def __init__(self, configfile, keysfile):
        self.os = openstack(configfile)
        self.keysfile = keysfile
    
    def event(self, maxhosts=25, sleepfactor=1):
        hosts = self.os.instances()
        logger.info(f'Running hosts: {[h.name for h in hosts]}')
        instances = instance(hosts, self.keysfile)
        status = instances.condor_status()
        tokill = []
        toretire = []

        for h in hosts:
            kill = not h.name in [s['host'] for s in status]
            if kill:
                tokill.append(h)
            else:
                if h.uptime > datetime.timedelta(hours=4):
                    toretire.append(h)

        logger.info(f'Will kill the hosts: {[h.name for h in tokill]}')
        self.os.delete(tokill)
        time.sleep(sleepfactor*20)

        retire_instances = instance(toretire, self.keysfile)
        logger.info(f'Will retire the hosts: {[h.name for h in toretire]}')
        retire_instances.condor_retire()

        n_newhosts = maxhosts - len(hosts)

        logger.info(f'Will create {max(0, n_newhosts)} new hosts')
        
        if n_newhosts > 0:
            name = 'spot-'+str(uuid.uuid4())
            self.os.create(name=name, max=n_newhosts)
            time.sleep(sleepfactor*120)

            allhosts = self.os.instances()
            newhosts = [h for h in allhosts if h.uptime < datetime.timedelta(minutes=10)]
            logger.info(f'{len(newhosts)} created with names {[h.name for h in newhosts]}')
            newinstances = instance(newhosts, self.keysfile)
            newinstances.configure()
