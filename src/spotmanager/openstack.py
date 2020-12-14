"""Manage the connections to the openstack API"""
import datetime
import dateutil.parser
import subprocess

from keystoneauth1 import session
from keystoneauth1.identity import v3
from novaclient.client import Client as nova_client

class openstack():


    def __init__(self, configfile):
        """Object that will manage the connections to openstack. You need to give the path to the file that
        contains the openstack RC."""

        proc = subprocess.Popen(['bash', '-c',
                                 f'source {configfile} && echo OS_AUTH_URL=$OS_AUTH_URL && echo OS_USERNAME=$OS_USERNAME && echo OS_PASSWORD=$OS_PASSWORD && echo OS_PROJECT_ID=$OS_PROJECT_ID && echo OS_USER_DOMAIN_NAME=$OS_USER_DOMAIN_NAME'],
                                stdout=subprocess.PIPE)
        env = {tup[0].strip(): tup[1].strip() for tup in map(lambda s: s.decode('utf-8').strip().split('=', 1),
                                                             proc.stdout)}
        auth = v3.Password(auth_url=env['OS_AUTH_URL'],
                           username=env['OS_USERNAME'],
                           password=env['OS_PASSWORD'],
                           project_id=env['OS_PROJECT_ID'],
                           user_domain_name=env['OS_USER_DOMAIN_NAME'])
        self.session = session.Session(auth=auth)
        self.nova = nova_client('2.1',session=self.session)

    def create(self, name='test', min=1, max=1):
        instance = self.nova.servers.create(name,
                                            image=self.nova.glance.find_image('NeCTAR CentOS 7 x86_64'),
                                            flavor=self.nova.flavors.find(name='m3.small'),
                                            nics = [{'net-id': self.nova.neutron.find_network('lhcb').id}],
                                            key_name='rsa',
                                            security_group='default',
                                            min_count=min,
                                            max_count=max)
        return instance

    def delete(self, servers):
        """Delete the servers in the list. The list can either be nova server objects or server objects
        as provided by the instances member function

        
        import spotmanager.openstack
        os =  spotmanager.openstack.openstack('myproject-openrc.sh')
        l = os.instances()
        os.delete(l)
        """
        for s in servers:
            s.delete()

    def instances(self):
        """Return a list of the servers for the project

        import spotmanager.openstack
        os =  spotmanager.openstack.openstack('myproject-openrc.sh')
        l = os.instances()
        
        The list elements are a simple objects that contain the link to a server object, the name,
        the status and the uptime.
        """

        class server():

            def __init__(self, server, name, status, uptime, ip):
                self.server = server
                self.name = name
                self.status = status
                self.uptime = uptime
                self.ip = ip

            def __str__(self):
                uphours = self.uptime.total_seconds() / 3600
                return f'Name: {self.name}, Status: {self.status}, Uptime = {uphours:.1f} hours, IP = {self.ip}'

            def __repr__(self):
                uphours = self.uptime.total_seconds() / 3600
                return f'server({repr(self.server)}, {self.name}, {self.status}, {repr(self.uptime)}, {self.ip})'

            def delete(self):
                self.server.delete()


        servers = []
        for s in self.nova.servers.list():
            start = s.created
            uptime = datetime.datetime.now(tz=datetime.timezone.utc)-dateutil.parser.isoparse(start)
            servers.append(server(s, s.name, s.status, uptime, s.networks['lhcb'][0]))
        return servers
        

