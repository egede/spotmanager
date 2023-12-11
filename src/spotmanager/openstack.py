"""Manage the connections to the openstack API"""
import datetime
import subprocess
import shutil
import tempfile
import logging
import dateutil.parser

from os.path import join, abspath, expanduser

from keystoneauth1 import session
from keystoneauth1.identity import v3
from novaclient.client import Client as nova_client
from novaclient.exceptions import Conflict

logger = logging.getLogger(__name__)

class openstack():


    def __init__(self, configfile):
        """Object that will manage the connections to openstack. You need to give the path to the file that
        contains the openstack RC."""

        abs_fname = abspath(expanduser(configfile))
        
        with tempfile.TemporaryDirectory() as tmpdirname:
            authfile = join(tmpdirname, 'authenticate')
            with open(authfile, 'w') as f:
                f.write(f'source {abs_fname}\n')
                f.write('echo OS_AUTH_URL=$OS_AUTH_URL\n')
                f.write('echo OS_USERNAME=$OS_USERNAME\n')
                f.write('echo OS_PASSWORD=$OS_PASSWORD\n')
                f.write('echo OS_PROJECT_ID=$OS_PROJECT_ID\n')
                f.write('echo OS_USER_DOMAIN_NAME=$OS_USER_DOMAIN_NAME\n')
            proc = subprocess.Popen(['bash', '-c', f'source {authfile}'], stdout=subprocess.PIPE)
            env = {tup[0].strip(): tup[1].strip() for tup in map(lambda s: s.decode('utf-8').strip().split('=', 1),
                                                             proc.stdout)}
            auth = v3.Password(auth_url=env['OS_AUTH_URL'],
                               username=env['OS_USERNAME'],
                               password=env['OS_PASSWORD'],
                               project_id=env['OS_PROJECT_ID'],
                               user_domain_name=env['OS_USER_DOMAIN_NAME'])

        self.session = session.Session(auth=auth)
        self.nova = nova_client('2.1',session=self.session)
        logger.info(f"Project is: user: {env['OS_USERNAME']}, project: {env['OS_PROJECT_ID']}, domain: {env['OS_USER_DOMAIN_NAME']}")

    def create(self, name='spot-test', min=1, max=1, zone=""):
        if len(zone)>0:
            instance = self.nova.servers.create(name,
                                                image=self.nova.glance.find_image('base-batch'),
                                                flavor=self.nova.flavors.find(name='p3.medium'),
                                                availability_zone=zone,
                                                nics = [{'net-id': self.nova.neutron.find_network('lhcb').id}],
                                                key_name='rsa',
                                                min_count=min,
                                                max_count=max)
        else:
            instance = self.nova.servers.create(name,
                                                image=self.nova.glance.find_image('base-batch'),
                                                flavor=self.nova.flavors.find(name='p3.medium'),
                                                nics = [{'net-id': self.nova.neutron.find_network('lhcb').id}],
                                                key_name='rsa',
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
            logger.debug(f'Deleting {s}')
            s.delete()

    def instances(self):
        """Return a list of the servers for the project

        import spotmanager.openstack
        os =  spotmanager.openstack.openstack('myproject-openrc.sh')
        l = os.instances()
        
        The list elements are a simple object that contain the link to a server object, the name,
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
                try:
                    self.server.delete()
                except Conflict as e:
                    logger.warning(f'Raised exception <{e}> when deleting the server {self.name}. Will just ignore.')

        servers = []
        for s in self.nova.servers.list():
            start = s.created
            uptime = datetime.datetime.now(tz=datetime.timezone.utc)-dateutil.parser.isoparse(start)
            if s.name[:5]=='spot-' and 'lhcb2' in s.networks:
                servers.append(server(s, s.name, s.status, uptime, s.networks['lhcb2'][0]))
        logger.debug(f'Instances: {[str(s) for s in servers]}')
        return servers
