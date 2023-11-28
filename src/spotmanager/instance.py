"""Manage the comunication with an Openstack instance"""
import subprocess
import re
import logging
import time

from os.path import basename

from pssh.clients.ssh.parallel import ParallelSSHClient
from pssh.exceptions import Timeout
from gevent import joinall

logger = logging.getLogger(__name__)

class instance():
    """Manage the communication with a set of Openstack instances. This includes the ability to configure
    them, run commands on them, check if they are active as Condor worker nodes etc."""

    def __init__(self, instances, keysfile):
        self.hosts = instances
        self.keysfile = keysfile
        logger.debug(f'Dealing with hosts {[h.name for h in self.hosts]}')

    def allowssh(self):
        """Allow ssh to the instances"""
        for host in self.hosts:
            ip = host.ip
            logger.info(f'Allowing ssh to {ip}.')
            subprocess.run(f'ssh-keygen -R {ip}', shell=True)
            subprocess.run(f'ssh-keyscan -H {ip} >> ~/.ssh/known_hosts', shell=True)

    def command(self, command, timeout=60, sudo=False):
        """Execute a command on the instances. This will be done using an ssh command and potentially with sudo"""
        logger.info(f'Executing {command} with sudo {sudo}.')
        client = ParallelSSHClient([i.ip for i in self.hosts], pkey=self.keysfile)
        try:
            output = client.run_command(command, sudo=sudo, stop_on_errors=False)
            client.join(output, timeout=timeout)

            for host_output in output:
                host = host_output.host
                if host_output.exception != None:
                    logger.error(f'Host {host} has exception: {host_output.exception}')

            return output
        except Exception as e:
            logger.error(f'Problem encountered with command: {command}')
            logger.error(f'Exception: {e}')

    def copy(self, fname):
        """Copy a file to all the instances."""
        client = ParallelSSHClient([i.ip for i in self.hosts], timeout=60, pkey=self.keysfile)
        logger.debug(f'Copy file {fname}.')
        cmds = client.copy_file(fname, basename(fname))
        joinall(cmds, raise_error=False)
        
    def configure(self):
        """Carry out the configuration of all the instances using a predefined configuration script and finishing
        with a reboot of all the instances (to upgrade the kernel)."""
        logger.info('Configuring hosts')

        self.allowssh()
        nwait = 5
        for i in range(nwait):
            try:
                ret = self.command('uptime')
                success = True
                for host_output in ret:
                    if host_output.exception != None:
                        success = False
                        break
                if success: break
            except:
                pass
            logger.info(f'Waiting for servers to go live {i}/{nwait}')
            time.sleep(30)

        self.command('timedatectl set-timezone Australia/Melbourne', timeout=60, sudo=True)
        self.command('dnf clean all', timeout=120, sudo=True)
        self.command('dnf update -y', timeout=1200, sudo=True)
        self.command('systemctl enable condor', timeout=1200, sudo=True)
        self.command('shutdown -r +1', timeout=120, sudo=True)
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


    def condor_queue(self):
        """Report on the job queue in Condor"""
        output = subprocess.run(['condor_q'], stdout=subprocess.PIPE, encoding='utf-8').stdout
        for line in output.split('\n'):
            match = re.match(
                r'^Total for all users: (?P<jobs>[\.0-9]+) jobs;'+
                r' (?P<completed>[\.0-9]+) completed,'+
                r' (?P<removed>[\.0-9]+) removed,'+
                r' (?P<idle>[\.0-9]+) idle,'+
                r' (?P<running>[\.0-9]+) running,'+
                r' (?P<held>[\.0-9]+) held,'+
                r' (?P<suspended>[\.0-9]+) suspended', line)
            if match:
                return dict([(k, int(v)) for k, v in match.groupdict().items()])
