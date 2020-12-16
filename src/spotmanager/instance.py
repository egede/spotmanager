"""Manage the comunication with an Openstack instance"""
import subprocess
import re

from os.path import basename

from pssh.clients import ParallelSSHClient
from pssh.exceptions import Timeout
from gevent import joinall

class instance():
    """Manage the communication with a set of Openstack instances. This includes the ability to configure
    them, run commands on them, check if they are active as Condor worker nodes etc."""

    def __init__(self, instances):
        self.hosts = instances
    
    def command(self, command, timeout=60, sudo=False):
        """Execute a command on the instances. This will be done using an ssh command and potentially with sudo"""
        client = ParallelSSHClient([i.ip for i in self.hosts])
        output = client.run_command(command, read_timeout=timeout, sudo=sudo)
        client.join()
        return output

    def copy(self, fname):
        """Copy a file to all the instances."""
        client = ParallelSSHClient([i.ip for i in self.hosts], timeout=60)
        cmds = client.copy_file(fname, basename(fname))
        joinall(cmds, raise_error=True)
        
    def configure(self):
        """Carry out the configuration of all the instances using a predefined configuration script and finishing
        with a reboot of all the instances (to upgrade the kernel)."""
        self.copy('spot-configure')

        print('Updating instances')
        self.command('yum -y update', timeout=600, sudo=True)
        print('Configuring instances')
        self.command('chmod +x ./spot-configure', timeout=600, sudo=True)
        self.command('./spot-configure', timeout=600, sudo=True)
        print('Rebooting instances')
        self.command('shutdown -r +1', sudo=True)

    def loadaverage(self):
        """Return a dictionary of the instances with the average load per cpu for each of them"""
        loads = {}
        output1 = self.command("uptime | awk -F'[a-z,]:' '{ print $2}' | awk -F',' '{ print $3}'")
        output2 = self.command("lscpu | grep ^CPU.s.: | cut -d : -f 2")
        for h, o1, o2 in zip(self.hosts, output1, output2):
            loads[h.name] = float(next(o1.stdout))/float(next(o2.stdout))
        return loads
        
    def condor_status(self):
        output = subprocess.run('condor_status', stdout=subprocess.PIPE, encoding='utf-8').stdout
        
        status = []
        for line in output.split('\n'):
            match = re.match(
                r'^slot[0-9]+@(?P<fullhost>(?P<host>[-0-9\w]+)[\.-0-9\w]+).*'+
                '(?P<state>Unclaimed|Claimed)\s+'+
                '(?P<activity>\w+).*?'+
                '(?P<load>[\.0-9]+)', line)
            if match:
                status.append(match.groupdict())
        return status

        
    def condor_retire(self):
        """Retire the instances from condor. This means that jobs keep running on them, but they will
        not accept new jobs."""
        status = self.condor_status()
        print('************************')
        print(status)
        print('************************')
        commands = {}
        for host in self.hosts:
            print(host.name)
            for s in status:
                if s['host']==host.name:
                    commands[host.name] = s['fullhost']
                    
        commandlist = [f"condor_off -startd -peaceful {c}" for c in commands.values()]
        print(commandlist)
        server = ['server']*len(commandlist)
        client = ParallelSSHClient(server)

        output = client.run_command('%s', host_args=commandlist, sudo=True) 
