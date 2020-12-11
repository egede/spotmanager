"""Manange instances in an openstack cloud"""
import datetime
import time

from spotmanager.openstack import openstack

class instance():

    def __init__(self, configfile):
        self.os = openstack(configfile)
    
    def event(self):
        # instances = self.os.instances()

        # tokill = []
        # tomute = []

        # for i in instances:
        #     if i.uptime > datetime.timedelta(hours=1):
        #         if busy(i)

    def start(self):
        print('start')

    def stop(self):
        print('stop')

    def busy(self):
        return True

    def uptime(self):
        return 0
