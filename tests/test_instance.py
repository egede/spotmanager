import unittest

from unittest import mock

from spotmanager.instance import instance

class InstanceTestCase(unittest.TestCase):

    class TestHost():
        def __init__(self, name, ip):
            self.name = name
            self.ip = ip

    @mock.patch('spotmanager.instance.ParallelSSHClient')
    def test_command(self, mock_ssh):

        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts)

        i.command('ls', timeout=1, sudo=True)

        mock_ssh.assert_called_with([hosts[0].ip, hosts[1].ip])
        self.assertIn(mock.call().run_command('ls', read_timeout=1, sudo=True), mock_ssh.mock_calls)

    @mock.patch('spotmanager.instance.ParallelSSHClient')
    def test_copy(self, mock_ssh):

        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts)

        i.copy('/foo/myfile')

        mock_ssh.assert_called_with([hosts[0].ip, hosts[1].ip], timeout=60)
        self.assertIn(mock.call().scp_send('/foo/myfile', 'myfile'), mock_ssh.mock_calls)

    @mock.patch('spotmanager.instance.instance.copy')
    @mock.patch('spotmanager.instance.instance.command')
    def test_configure(self, mock_command, mock_copy):

        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts)

        i.configure()

        mock_copy.assert_called()
        assert(mock_command.call_count==3)


    @mock.patch('spotmanager.instance.instance.command')
    def test_loadaverage(self, mock_command):

        
        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts)

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
        i = instance(hosts)

        mock_run.return_value.stdout= """
Name                   OpSys      Arch   State     Activity LoadAv Mem   ActvtyTime

slot1@batch.novalocal  LINUX      X86_64 Claimed   Busy      1.030 2000  0+00:18:31
slot2@batch.novalocal  LINUX      X86_64 Claimed   Busy      1.030 2000  0+04:16:28
slot3@batch.novalocal  LINUX      X86_64 Claimed   Busy      1.030 2000  0+02:11:51
slot4@batch.novalocal  LINUX      X86_64 Claimed   Busy      1.030 2000  0+05:53:34
slot5@batch.novalocal  LINUX      X86_64 Claimed   Busy      1.030 2000  0+11:37:59
slot6@batch.novalocal  LINUX      X86_64 Claimed   Busy      1.030 2000  0+09:10:35
slot7@batch.novalocal  LINUX      X86_64 Claimed   Busy      1.030 2000  0+05:26:49
slot8@batch.novalocal  LINUX      X86_64 Claimed   Busy      1.030 2000  0+00:38:31
slot9@batch.novalocal  LINUX      X86_64 Claimed   Busy      1.030 2000  0+02:06:51
slot10@batch.novalocal LINUX      X86_64 Claimed   Busy      1.030 2000  0+04:47:28
slot11@batch.novalocal LINUX      X86_64 Claimed   Busy      1.030 2000  0+05:59:54
slot12@batch.novalocal LINUX      X86_64 Claimed   Busy      1.030 2000  0+06:26:49
slot13@batch.novalocal LINUX      X86_64 Claimed   Busy      1.030 2000  0+02:28:31
slot14@batch.novalocal LINUX      X86_64 Claimed   Busy      1.030 2000  0+07:57:59
slot15@batch.novalocal LINUX      X86_64 Claimed   Busy      1.030 2000  0+06:47:32
slot16@batch.novalocal LINUX      X86_64 Claimed   Busy      1.030 2000  0+07:11:54
slot1@batch2.novalocal LINUX      X86_64 Claimed   Retired   1.020 1985  0+10:47:10
slot2@batch2.novalocal LINUX      X86_64 Claimed   Retired   1.020 1985  0+04:42:01
slot3@batch2.novalocal LINUX      X86_64 Claimed   Retired   1.020 1985  0+05:15:22
slot4@batch2.novalocal LINUX      X86_64 Claimed   Retired   1.020 1985  0+16:24:31
slot5@batch2.novalocal LINUX      X86_64 Claimed   Retired   1.020 1985  0+07:30:12
slot6@batch2.novalocal LINUX      X86_64 Claimed   Retired   1.020 1985  0+16:05:36
slot7@batch2.novalocal LINUX      X86_64 Claimed   Retired   1.020 1985  0+14:38:35
slot8@batch2.novalocal LINUX      X86_64 Claimed   Retired   1.020 1985  0+03:24:25

               Machines Owner Claimed Unclaimed Matched Preempting  Drain

  X86_64/LINUX       24     0      24         0       0          0      0

         Total       24     0      24         0       0          0      0
"""

        status = i.condor_status()

        assert(mock_run.call_count==1)
        assert(status=={'batch':'Busy', 'batch2':'Retired'})


    @mock.patch('spotmanager.instance.ParallelSSHClient')
    def test_condor_retire(self, mock_ssh):

        hosts = [InstanceTestCase.TestHost('test1','192.168.0.1'),
                 InstanceTestCase.TestHost('test2', '192.168.0.2')]
        i = instance(hosts)

        i.condor_retire()

        mock_ssh.assert_called_with(['server', 'server'])
        self.assertIn(mock.call().run_command('%s', host_args=['condor_off -startd -peaceful test1', 'condor_off -startd -peaceful test2'], sudo=True), mock_ssh.mock_calls)
