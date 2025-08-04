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
    
    def event(self, maxhosts=25, sleepfactor=1, remove=False, zone='', throttle=-1, flavour=''):
        hosts = self.os.instances()
        logger.info(f'Running hosts: {[h.name for h in hosts]}')
        instances = instance(hosts, self.keysfile)
        status = instances.condor_status()
        pilot_fails = instances.pilot_fails()
        tokill = []
        toretire = []

        for h in hosts:
            kill = (h.name[:7]=='batch-p') and (not h.name in [s['host'] for s in status])
            if kill:
                tokill.append(h)
            else:
                if (h.name[:7]=='batch-p') and h.uptime > datetime.timedelta(hours=4):
                    toretire.append(h)
            if h.name in pilot_fails:
                logger.info(f'Pilot failed on {h.name} - will kill')
                if not kill:
                    tokill.append(h)
        if len(tokill)>0:
            if remove:
                logger.info(f'Will kill the hosts: {[h.name for h in tokill]} - pausing for {sleepfactor} minute(s).')
                self.os.delete(tokill)
                time.sleep(sleepfactor*60)
            else:
                logger.info(f'Will not kill the hosts: {[h.name for h in tokill]} - remove is set to False')
        else:
            logger.info('No instances to kill')

        retire_instances = instance(toretire, self.keysfile)
        if remove:
            logger.info(f'Will retire the hosts: {[h.name for h in toretire]}')
            retire_instances.condor_retire()
        else:
            logger.info(f'Will not retire the hosts: {[h.name for h in toretire]} - remove is set to False')

        n_newhosts = min(maxhosts - len(hosts) + len(tokill), (instances.condor_queue()['idle'] -1) // 2 + 1)
        if throttle>=0:
            n_newhosts = min(n_newhosts, throttle)
        
        logger.info(f'Will create {max(0, n_newhosts)} new hosts')
        
        if n_newhosts > 0:
            name = 'batch-'+flavour+"-"+str(uuid.uuid4())
            self.os.create(name=name, max=n_newhosts, zone=zone, flavour=flavour)
            for i in range(5*sleepfactor):
                time.sleep(60)
                try:
                    allhosts = self.os.instances()
                    newhosts = [h for h in allhosts if h.uptime < datetime.timedelta(minutes=9)]
                except Exception as e:
                    logger.error(f'Failed to connect to Openstack with error {e}')
                    newhosts = []
                if len(newhosts) >= n_newhosts:
                    break
                logger.info(f'{len(newhosts)}/{n_newhosts} created')
            logger.info(f'{len(newhosts)} created with names {[h.name for h in newhosts]}')
            if (len(newhosts) >0):
                newinstances = instance(newhosts, self.keysfile)
                newinstances.configure()
