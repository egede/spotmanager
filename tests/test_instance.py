import unittest
import pytest

from unittest import mock

from spotmanager.instance import instance

from pssh.exceptions import Timeout

class InstanceTestCase(unittest.TestCase):

    class TestHost():
        def __init__(self, name, ip):
            self.name = name
            self.ip = ip

    @mock.patch('spotmanager.instance.ParallelSSHClient')
    def test_command(self, mock_ssh):

        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts, '~/.ssh/nokey')

        m = mock.Mock()
        m1 = mock.Mock()
        m2 = mock.Mock()
        m3 = mock.Mock()
        mock_ssh.return_value = m
        m.run_command.side_effect = m1
        m1.return_value = [m3]
        m.join.side_effect = m2
        ret = i.command('ls', timeout=1, sudo=True)

        mock_ssh.assert_called_with([hosts[0].ip, hosts[1].ip], pkey='~/.ssh/nokey')
        m1.assert_called_with('ls', sudo=True, stop_on_errors=False)
        m2.assert_called_with([m3], timeout=1)
        assert(ret == [m3])

    @mock.patch('spotmanager.instance.ParallelSSHClient')
    def test_command_fail(self, mock_ssh):

        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts, '~/.ssh/nokey')

        m = mock.Mock()
        m1 = mock.Mock()
        m2 = mock.Mock()
        m3 = mock.Mock()
        m3.exception.return_value=Exception()
        mock_ssh.return_value = m
        m.run_command.side_effect = m1
        m1.return_value = [m3]
        m.join.side_effect = m2
        ret = i.command('ls', timeout=1, sudo=True)

        m2.assert_called_with([m3], timeout=1)
        assert(ret == [m3])

        
    @mock.patch('spotmanager.instance.ParallelSSHClient')
    def test_command_timeout(self, mock_ssh):

        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts, '~/.ssh/nokey')

        m = mock.Mock()
        m1 = mock.Mock()
        m2 = mock.Mock()
        m3 = mock.Mock()
        mock_ssh.return_value = m
        m.run_command.side_effect = m1
        m1.return_value = m3
        m.join.side_effect = Timeout
        ret = i.command('ls', timeout=1, sudo=True)
        
        assert(ret == None)


    @mock.patch('spotmanager.instance.ParallelSSHClient')
    def test_copy(self, mock_ssh):

        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts, '~/.ssh/nokey')

        i.copy('/foo/myfile')

        mock_ssh.assert_called_with([hosts[0].ip, hosts[1].ip],
                                    timeout=60, pkey='~/.ssh/nokey')
        self.assertIn(mock.call().copy_file('/foo/myfile', 'myfile'), mock_ssh.mock_calls)

    @mock.patch('spotmanager.instance.instance.copy')
    @mock.patch('spotmanager.instance.instance.command')
    def test_configure(self, mock_command, mock_copy):

        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts, '~/.ssh/nokey')

        i.configure()

        mock_copy.assert_called()
        assert(mock_command.call_count==4)


    @mock.patch('spotmanager.instance.instance.command')
    def test_loadaverage(self, mock_command):

        
        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts, '~/.ssh/nokey')

        m1 = mock.Mock()
        m1.stdout=iter(['12.3'])
        m2 = mock.Mock()
        m2.stdout=iter(['45.6'])
        m3 = mock.Mock()
        m3.stdout=iter(['10'])
        m4 = mock.Mock()
        m4.stdout=iter(['100'])

        mock_command.side_effect = [[m1, m2], [m3, m4]]
        
        loads = i.loadaverage()

        assert(mock_command.call_count==2)
        assert(loads=={'test1':1.23, 'test2':0.456})
        
    @mock.patch('spotmanager.instance.subprocess.run')
    def test_condor_status(self, mock_run):

        
        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts, '~/.ssh/nokey')

        mock_run.return_value.stdout= """
Name                   OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime

slot14@batch.novalocal LINUX      X86_64 Claimed     Idle      0.000 2000  0+07:57:59
slot15@batch.novalocal LINUX      X86_64 Claimed     Busy      1.030 2000  0+06:47:32
slot16@batch.novalocal LINUX      X86_64 Claimed     Busy      1.030 2000  0+07:11:54
slot1@batch2.novalocal LINUX      X86_64 Unclaimed   Retired   1.020 1985  0+10:47:10
slot2@batch2.novalocal LINUX      X86_64 Claimed     Retired   1.020 1985  0+04:42:01


               Machines Owner Claimed Unclaimed Matched Preempting  Drain

  X86_64/LINUX       24     0      24         0       0          0      0

         Total       24     0      24         0       0          0      0
"""

        status = i.condor_status()

        assert(mock_run.call_count==1)
        assert(status==[
            {'fullhost':'batch.novalocal', 'host':'batch', 'state':'Claimed', 'activity':'Idle', 'load': '0.000'},
            {'fullhost':'batch.novalocal', 'host':'batch', 'state':'Claimed', 'activity':'Busy', 'load': '1.030'},
            {'fullhost':'batch.novalocal', 'host':'batch', 'state':'Claimed', 'activity':'Busy', 'load': '1.030'},
            {'fullhost':'batch2.novalocal', 'host':'batch2', 'state':'Unclaimed', 'activity':'Retired',
             'load': '1.020'},
            {'fullhost':'batch2.novalocal', 'host':'batch2', 'state':'Claimed', 'activity':'Retired',
             'load': '1.020'},
        ])

    @mock.patch('spotmanager.instance.instance.condor_status')
    @mock.patch('spotmanager.instance.ParallelSSHClient')
    def test_condor_retire(self, mock_ssh, mock_condor_status):

        hosts = [InstanceTestCase.TestHost('batch','192.168.0.1'),
                 InstanceTestCase.TestHost('batch2', '192.168.0.2')]
        i = instance(hosts, '~/.ssh/nokey')

        mock_condor_status.side_effect=[ [
            {'fullhost':'batch.novalocal', 'host':'batch', 'state':'Claimed', 'activity':'Idle', 'load': '0.000'},
            {'fullhost':'batch.novalocal', 'host':'batch', 'state':'Claimed', 'activity':'Busy', 'load': '1.030'},
            {'fullhost':'batch.novalocal', 'host':'batch', 'state':'Claimed', 'activity':'Busy', 'load': '1.030'},
            {'fullhost':'batch2.novalocal', 'host':'batch2', 'state':'Unclaimed', 'activity':'Retired',
             'load': '1.020'},
            {'fullhost':'batch2.novalocal', 'host':'batch2', 'state':'Claimed', 'activity':'Retired',
             'load': '1.020'},
        ] ]  

        i.condor_retire()

        mock_ssh.assert_called_with(['server', 'server'], pkey='~/.ssh/nokey')
        self.assertIn(mock.call().run_command('%s',
                                              host_args=['condor_off -startd -peaceful batch.novalocal',
                                                         'condor_off -startd -peaceful batch2.novalocal'],
                                              sudo=True),
                      mock_ssh.mock_calls)
