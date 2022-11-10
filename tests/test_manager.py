import unittest
import datetime

from unittest import mock

from spotmanager.manager import manager


class ManagerTestCase(unittest.TestCase):

    @mock.patch('spotmanager.manager.openstack')
    def test_instantiate(self, mock_os):

        ma = manager('foo/bar.rc', '~/.ssh/nokey')

        mock_os.assert_called_with('foo/bar.rc')
        self.assertTrue(hasattr(ma, 'os'))

    @mock.patch('spotmanager.manager.instance')
    @mock.patch('spotmanager.manager.openstack')
    def test_event(self, mock_os, mock_instance):

        ma = manager('for/bar.rc', '~/.ssh/nokey')

        m1 = mock.Mock() # Should retire
        m1.name = 'test1'
        m1.uptime = datetime.timedelta(hours=10)
        m2 = mock.Mock() # Should kill
        m2.name = 'test2'
        m2.uptime = datetime.timedelta(hours=23)
        m3 = mock.Mock() # Should keep
        m3.name = 'test3'
        m3.uptime = datetime.timedelta(minutes=30)

        m5 = mock.Mock() # Should be ignored (not in status list)
        m5.name = 'test5'
        m5.uptime = datetime.timedelta(minutes=1)

        m_instances = mock.Mock()

        m_instances.condor_status.side_effect=[ [
            {'fullhost':'test1.novalocal', 'host':'test1', 'state':'Claimed', 'activity':'Busy', 'load': '3.000'},
            {'fullhost':'test3.novalocal', 'host':'test3', 'state':'Unclaimed', 'activity':'Idle', 'load': '0.020'},
        ] ]  

        m_instances.condor_queue.side_effect=[{'jobs': 51, 
            'completed': 2,
            'removed': 37,
            'idle': 19,
            'running': 39,
            'held': 12,
            'suspended': 1}]

        m_instances_retire = mock.Mock()

        m_instances_new = mock.Mock()
        
        ma.os.instances.side_effect = [[m1, m2, m3], [m3, m5]]
        mock_instance.side_effect = [ m_instances, m_instances_retire, m_instances_new ]
        
        ma.event(sleepfactor=0.001, remove=True)

        ma.os.delete.assert_called_with([m2])
        m_instances_retire.condor_retire.assert_called()

        calls = [mock.call([m1, m2, m3], '~/.ssh/nokey'), mock.call([m1], '~/.ssh/nokey'),
                 mock.call([m5], '~/.ssh/nokey')]
        mock_instance.assert_has_calls(calls)
        m_instances_new.configure.assert_called_once()


    @mock.patch('spotmanager.manager.instance')
    @mock.patch('spotmanager.manager.openstack')
    def test_event_nokill(self, mock_os, mock_instance):
        ma = manager('for/bar.rc', '~/.ssh/nokey')

        m2 = mock.Mock() # Should kill
        m2.name = 'test2'
        m2.uptime = datetime.timedelta(hours=23)

        m5 = mock.Mock() # Should be ignored (not in status list)
        m5.name = 'test5'
        m5.uptime = datetime.timedelta(minutes=1)

        m_instances = mock.Mock()

        m_instances.condor_status.side_effect=[ [
            {'host':'test1',  'load': '3.000'},
            {'host':'test3', 'load': '0.020'},
        ] ]  

        m_instances.condor_queue.side_effect=[{'jobs': 51, 
            'completed': 2,
            'removed': 37,
            'idle': 19,
            'running': 39,
            'held': 12,
            'suspended': 1}]

        m_instances_retire = mock.Mock()

        m_instances_new = mock.Mock()
        
        ma.os.instances.side_effect = [[m2], [m5]]
        mock_instance.side_effect = [ m_instances, m_instances_retire, m_instances_new ]
        
        ma.event(sleepfactor=0.001, remove=False)

        ma.os.delete.assert_called_with([])
        
        calls = [mock.call([m2], '~/.ssh/nokey'), mock.call([], '~/.ssh/nokey'),
                 mock.call([m5], '~/.ssh/nokey')]
        mock_instance.assert_has_calls(calls)
        m_instances_new.configure.assert_called_once()


    @mock.patch('spotmanager.manager.instance')
    @mock.patch('spotmanager.manager.openstack')
    def test_throttle(self, mock_os, mock_instance):

        ma = manager('for/bar.rc', '~/.ssh/nokey')

        m_instances = mock.Mock()
        m_instances_retire = mock.Mock()

        m_instances.condor_status.side_effect=[ [ ] ]  

        m_instances_new = mock.Mock()

        m_instances.condor_queue.side_effect=[{'jobs': 51, 
            'completed': 2,
            'removed': 37,
            'idle': 19,
            'running': 39,
            'held': 12,
            'suspended': 1}]

        mock_instance.side_effect = [ m_instances, m_instances_retire, m_instances_new ]
        
        m1 = mock.Mock()
        ma.os.create=m1

        ma.event(sleepfactor=0.001, throttle=1)

        m1.assert_called_with(max=1, zone=mock.ANY, name=mock.ANY)

    @mock.patch('spotmanager.manager.instance')
    @mock.patch('spotmanager.manager.openstack')
    def test_no_throttle(self, mock_os, mock_instance):

        ma = manager('for/bar.rc', '~/.ssh/nokey')

        m_instances = mock.Mock()
        m_instances_retire = mock.Mock()

        m_instances.condor_status.side_effect=[ [ ] ]  

        m_instances_new = mock.Mock()

        m_instances.condor_queue.side_effect=[{'jobs': 51, 
            'completed': 2,
            'removed': 37,
            'idle': 30,
            'running': 39,
            'held': 12,
            'suspended': 1}]

        mock_instance.side_effect = [ m_instances, m_instances_retire, m_instances_new ]
        
        m1 = mock.Mock()
        ma.os.create=m1

        ma.event(sleepfactor=0.001)

        m1.assert_called_with(max=25, zone=mock.ANY, name=mock.ANY)


    @mock.patch('spotmanager.manager.instance')
    @mock.patch('spotmanager.manager.openstack')
    def test_few_idle(self, mock_os, mock_instance):

        ma = manager('for/bar.rc', '~/.ssh/nokey')

        m_instances = mock.Mock()
        m_instances_retire = mock.Mock()

        m_instances.condor_status.side_effect=[ [ ] ]  

        m_instances_new = mock.Mock()

        m_instances.condor_queue.side_effect=[{'jobs': 51, 
            'completed': 2,
            'removed': 37,
            'idle': 10,
            'running': 39,
            'held': 12,
            'suspended': 1}]

        mock_instance.side_effect = [ m_instances, m_instances_retire, m_instances_new ]
        
        m1 = mock.Mock()
        ma.os.create=m1

        ma.event(sleepfactor=0.001)

        m1.assert_called_with(max=10, zone=mock.ANY, name=mock.ANY)
