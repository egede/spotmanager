"""Manange instances in an openstack cloud"""
import datetime
import time
import uuid

from spotmanager.openstack import openstack
from spotmanager.instance import instance

class manager():

    def __init__(self, configfile):
        self.os = openstack(configfile)
    
    def event(self, maxhosts=25, sleepfactor=1):
        hosts = self.os.instances()
        instances = instance(hosts)
        loads = instances.loadaverage()
        status = instances.condor_status()
        tokill = []
        toretire = []

        for h in hosts:
            print(h.name)
            try:
                if status[h.name] == 'Retired' and loads[h.name]<0.1:
                    tokill.append(h)
                    continue
                if status[h.name] == 'Busy' and h.uptime > datetime.timedelta(hours=1):
                    toretire.append(h)
            except KeyError:
                print(f'The host {h.name} is not running Condor or is not responding. Will kill it')
                tokill.append(h)

        self.os.delete(tokill)
        time.sleep(sleepfactor*20)

        retire_instances = instance(toretire)
        retire_instances.condor_retire()

        n_newhosts = maxhosts - len(hosts)

        name = 'spot-'+str(uuid.uuid4())
        self.os.create(name=name, max=n_newhosts)
        time.sleep(sleepfactor*120)

        allhosts = self.os.instances()
        newhosts = [h for h in allhosts if h.uptime < datetime.timedelta(minutes=10)]
        newinstances = instance(newhosts)
        newinstances.configure()
