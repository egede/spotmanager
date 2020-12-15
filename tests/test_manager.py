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
        m1.uptime = datetime.timedelta(hours=2)
        m2 = mock.Mock() # Should kill
        m2.name = 'test2'
        m2.uptime = datetime.timedelta(hours=23)
        m3 = mock.Mock() # Should keep
        m3.name = 'test3'
        m3.uptime = datetime.timedelta(minutes=30)
        m4 = mock.Mock() # Should kill (not in status list)
        m4.name = 'test4'
        m4.uptime = datetime.timedelta(hours=0.1)
        m5 = mock.Mock() # Should kill (not in status list)
        m5.name = 'test5'
        m5.uptime = datetime.timedelta(minutes=1)

        m_instances = mock.Mock()
        m_instances.loadaverage.side_effect=[{'test1':1.5, 'test2':0.01, 'test3':0.01, 'test4':0.00} ]
        m_instances.condor_status.side_effect=[{'test1':'Busy', 'test2':'Retired', 'test3':'Busy'} ]

        m_instances_retire = mock.Mock()

        m_instances_new = mock.Mock()
        
        ma.os.instances.side_effect = [[m1, m2, m3, m4], [m3, m5]]
        mock_instance.side_effect = [ m_instances, m_instances_retire, m_instances_new ]
        
        ma.event(sleepfactor=0.001)

        ma.os.delete.assert_called_with([m2, m4])
        m_instances_retire.condor_retire.assert_called()

        calls = [mock.call([m1, m2, m3, m4]), mock.call([m1]), mock.call([m5])]
        mock_instance.assert_has_calls(calls)
        m_instances_new.configure.assert_called_once()
