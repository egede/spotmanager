import unittest
import datetime

from unittest import mock

from spotmanager.manager import manager


class ManagerTestCase(unittest.TestCase):

    @mock.patch('spotmanager.manager.openstack')
    def test_instantiate(self, mock_os):

        ma = manager('foo/bar.rc')

        mock_os.assert_called_with('foo/bar.rc')
        self.assertTrue(hasattr(ma, 'os'))

    @mock.patch('spotmanager.manager.instance')
    @mock.patch('spotmanager.manager.openstack')
    def test_event(self, mock_os, mock_instance):

        ma = manager('for/bar.rc')

        m1 = mock.Mock() # Should retire
        m1.name = 'test1'
        m1.uptime = datetime.timedelta(hours=10)
        m2 = mock.Mock() # Should kill
        m2.name = 'test2'
        m2.uptime = datetime.timedelta(hours=23)
        m3 = mock.Mock() # Should keep
        m3.name = 'test3'
        m3.uptime = datetime.timedelta(minutes=30)

        m5 = mock.Mock() # Should kill (not in status list)
        m5.name = 'test5'
        m5.uptime = datetime.timedelta(minutes=1)

        m_instances = mock.Mock()

        m_instances.condor_status.side_effect=[ [
            {'fullhost':'test1.novalocal', 'host':'test1', 'state':'Claimed', 'activity':'Busy', 'load': '3.000'},
            {'fullhost':'test3.novalocal', 'host':'test3', 'state':'Unclaimed', 'activity':'Idle', 'load': '0.020'},
        ] ]  

        m_instances_retire = mock.Mock()

        m_instances_new = mock.Mock()
        
        ma.os.instances.side_effect = [[m1, m2, m3], [m3, m5]]
        mock_instance.side_effect = [ m_instances, m_instances_retire, m_instances_new ]
        
        ma.event(sleepfactor=0.001)

        ma.os.delete.assert_called_with([m2])
        m_instances_retire.condor_retire.assert_called()

        calls = [mock.call([m1, m2, m3]), mock.call([m1]), mock.call([m5])]
        mock_instance.assert_has_calls(calls)
        m_instances_new.configure.assert_called_once()
