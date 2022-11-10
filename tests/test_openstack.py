import unittest
import tempfile
import os.path

from unittest import mock

import novaclient
from spotmanager.openstack import openstack
from novaclient.exceptions import Conflict


class OpenstackTestCase(unittest.TestCase):

    @mock.patch('spotmanager.openstack.nova_client')
    @mock.patch('keystoneauth1.session.Session')
    @mock.patch('keystoneauth1.identity.v3.Password')
    def setUp(self, mock_v3, mock_session, mock_nova):
        self.td = tempfile.TemporaryDirectory()
        fname = os.path.join(self.td.name, 'test.rc')
        with open(fname, "w") as f:
            f.write("""
            # A test object 
            export OS_AUTH_URL=test
            export OS_USERNAME=test
            export OS_PASSWORD=test
            export OS_PROJECT_ID=test
            export OS_USER_DOMAIN_NAME=test""")

        self.os = openstack(fname)

        mock_v3.assert_called()
        mock_session.assert_called()
        mock_nova.assert_called()

        class tmp():
            def __init__(self):
                self.networks = {'lhcb':['192.168.0.1']}
                self.status='TEST'
                self.name='spot-test'
                self.created = '2020-12-08T04:31:54Z'

            def delete(self):
                pass
                
        self.os.nova.servers.list.return_value = [tmp(), tmp()]
        
    def tearDown(self):
        self.td.cleanup()

    def test_create(self):
        instance = self.os.create()
        instance = self.os.create(zone='foo')
        
    def test_instances(self):
        instances = self.os.instances()
        assert(len(instances) == 2)
        assert(instances[0].name=='spot-test')
        assert(instances[0].status=='TEST')
        assert(instances[0].ip=='192.168.0.1')

    def test_delete(self):
        instances = self.os.instances()
        self.os.delete(instances)
        self.os.delete([instances[0]])
        self.os.delete([instances[0].server])




class OpenstackFailTestCase(unittest.TestCase):

    @mock.patch('spotmanager.openstack.nova_client')
    @mock.patch('keystoneauth1.session.Session')
    @mock.patch('keystoneauth1.identity.v3.Password')
    def setUp(self, mock_v3, mock_session, mock_nova):
        self.td = tempfile.TemporaryDirectory()
        fname = os.path.join(self.td.name, 'test.rc')
        with open(fname, "w") as f:
            f.write("""
            # A test object 
            export OS_AUTH_URL=test
            export OS_USERNAME=test
            export OS_PASSWORD=test
            export OS_PROJECT_ID=test
            export OS_USER_DOMAIN_NAME=test""")

        self.os = openstack(fname)

        mock_v3.assert_called()
        mock_session.assert_called()
        mock_nova.assert_called()

        class tmp():
            def __init__(self):
                self.networks = {'lhcb':['192.168.0.1']}
                self.status='TEST'
                self.name='spot-test'
                self.created = '2020-12-08T04:31:54Z'

            def delete(self):
                raise Conflict(404)

        self.os.nova.servers.list.return_value = [tmp(), tmp()]

    def tearDown(self):
        self.td.cleanup()

    @mock.patch('spotmanager.openstack.logger.warning')
    def test_delete_fail(self, mock_warning):

        instances = self.os.instances()
        self.os.delete([instances[0]])
        mock_warning.assert_called_with('Raised exception <Conflict (HTTP 404)> when deleting the server spot-test. Will just ignore.')
