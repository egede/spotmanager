"""Manange instances in an openstack cloud"""
class Instance():

    def start(self):
        print('start')

    def stop(self):
        print('stop')

    def busy(self):
        return True

    def uptime(self):
        return 0
