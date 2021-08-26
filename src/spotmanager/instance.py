"""Manage the comunication with an Openstack instance"""
import subprocess
import re
import logging
import time

from os.path import basename

from pssh.clients import ParallelSSHClient
from pssh.exceptions import Timeout
from gevent import joinall

logger = logging.getLogger(__name__)

class instance():
    """Manage the communication with a set of Openstack instances. This includes the ability to configure
    them, run commands on them, check if they are active as Condor worker nodes etc."""

    def __init__(self, instances, keysfile):
        self.hosts = instances
        self.keysfile = keysfile
        logger.debug('Dealing with hosts {[h.name for h in self.hosts]}')
        
    def command(self, command, timeout=60, sudo=False):
        """Execute a command on the instances. This will be done using an ssh command and potentially with sudo"""
        logger.debug(f'Executing {command} with sudo {sudo}.')
        client = ParallelSSHClient([i.ip for i in self.hosts], pkey=self.keysfile)
        output = client.run_command(command, sudo=sudo)
        try:
            client.join(output, timeout=timeout)
            return output
        except Exception as e:
            logger.error(f'Timeout of {timeout} seconds encountered with command: {command}')
            logger.error(f'Exception: {e}')

    def copy(self, fname):
        """Copy a file to all the instances."""
        client = ParallelSSHClient([i.ip for i in self.hosts], timeout=60, pkey=self.keysfile)
        logger.debug(f'Copy file {fname}.')
        cmds = client.copy_file(fname, basename(fname))
        joinall(cmds, raise_error=True)
        
    def configure(self):
        """Carry out the configuration of all the instances using a predefined configuration script and finishing
        with a reboot of all the instances (to upgrade the kernel)."""
        logger.info('Configuring hosts')

        nwait = 50
        for i in range(nwait):
            try:
                ret = self.command('uptime')
                if (ret != None): break
            except:
                logger.info(f'Waiting for servers to go live {i}/{nwait}')
            time.sleep(30)

        self.copy('spot-configure')
        self.command('chmod a+x ./spot-configure', timeout=600)
        self.command('./spot-configure', timeout=1800, sudo=True)
        logger.info('Rebooting hosts')
        self.command('shutdown -r +1', sudo=True)
        logger.info('Done')
        
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
                r'(?P<state>Unclaimed|Claimed)\s+'+
                r'(?P<activity>\w+).*?'+
                r'(?P<load>[\.0-9]+)', line)
            if match:
                status.append(match.groupdict())
        logger.debug(status)
        return status

        
    def condor_retire(self):
        """Retire the instances from condor. This means that jobs keep running on them, but they will
        not accept new jobs."""
        status = self.condor_status()
        commands = {}
        for host in self.hosts:
            for s in status:
                if s['host']==host.name:
                    commands[host.name] = s['fullhost']
                    
        commandlist = [f"condor_off -startd -peaceful {c}" for c in commands.values()]
        logger.debug(commandlist)
        server = ['server']*len(commandlist)
        client = ParallelSSHClient(server, pkey=self.keysfile)

        output = client.run_command('%s', host_args=commandlist, sudo=True) 
