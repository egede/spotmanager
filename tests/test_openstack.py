import unittest
import tempfile
import os.path

from unittest import mock

from spotmanager.openstack import openstack

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

        m = mock.Mock()
        m.status='TEST'
        m.name='test'
        m.created = '2020-12-08T04:31:54Z'
        self.os.nova.servers.list.return_value = [m, m]
        
    def tearDown(self):
        self.td.cleanup()

    def test_create(self):
        instance = self.os.create()
        
    def test_instances(self):
        instances = self.os.instances()
        assert(len(instances) == 2)
        assert(instances[0].name=='test')
        assert(instances[0].status=='TEST')

    def test_delete(self):
        instances = self.os.instances()
        print(instances)
        self.os.delete(instances)
        self.os.delete([instances[0]])
        self.os.delete([instances[0].server])
