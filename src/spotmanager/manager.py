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

        self.os.delete(tokill)
        print('The following servers could be killed')
        for h in tokill:
            print(h)
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
