"""Manage the comunication with an instance"""
from os.path import basename

from pssh.clients import ParallelSSHClient
from gevent import joinall

class instance():

    def __init__(self, instances):
        self.hosts = [i.ip for i in instances]
    
    def command(self, command, timeout=60):
        """Cary out a command on the instances. This will be done using an ssh command and using sudo"""
        client = ParallelSSHClient(hosts)

        output = client.run_command(command, pkey='~/.ssh/my_pkey', read_timeout=timeout, sudo=True)

        return output
        # for host_out in output:
        #     try:
        #         for line in host_out.stdout:
        #             print(line)
        #         for line in host_out.stderr:
        #             print(line)
        #     except Timeout:
        #         pass


    def copy(self, fname):
        """Copy a file to all the instances."""
        client = ParallelSSHClient(hosts, timeout=60)
        cmds = client.scp_send(fname, basename(fname))
        joinall(cmds, raise_error=True)
        
    def configure(self):
        self.copy('spot-configure')

        self.command('yum -y update')
        self.command('./spot-configure', timeout=600)
        self.command('shutdown -r now')

    def load(self):
        loads = []
        output = self.command("uptime | awk -F'[a-z,]:' '{ print $2}' | awk -F',' '{ print $3}'")
        for ip, o in zip(self.hosts, host.output):
            try:
                loads.append([ip, float(o.stdout.read())])
            except Timeout:
                pass
        return loads
        
    def condor_status(self):
        return True


    def condor_retire(self):
        "condor_off -startd -peaceful 192.168.0.19"
        pass
