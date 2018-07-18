# coding: utf-8
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory.host import Host
from callback_mongo import ResultCallback, ResultModel


class ExecPlaybook(object):

    def __init__(self, playbooks=[], track_id=None):
        ResultModel().inster({
            "track_id": track_id,
            "status": "init"
        })
        self.playbooks = playbooks
        self.track_id = track_id
        self.Options = namedtuple('Options',
                                  ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection', 'module_path', 'forks',
                                   'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args',
                                   'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user',
                                   'verbosity', 'check', 'diff'])
        self.options = self.Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh',
                                    module_path=None,
                                    forks=50, remote_user='root', private_key_file=None, ssh_common_args=None,
                                    ssh_extra_args=None,
                                    sftp_extra_args=None, scp_extra_args=None, become=True, become_method=None,
                                    become_user='root',
                                    verbosity=None, check=False, diff=False)
        self.loader = DataLoader()

        self.passwords = dict(vault_pass='secret')

        self.inventory = InventoryManager(loader=self.loader, sources='')

        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)

    def add_host(self, host, port=None, user=None, passwd=None, private_file=None):
        h = Host(host, port)
        self.inventory.add_host(host, 'all', port)
        self.inventory.add_host(host, 'all', port)
        if user:
            self.variable_manager.set_host_variable(h, 'ansible_ssh_user', user)
        if passwd:
            self.variable_manager.set_host_variable(h, 'ansible_ssh_pass', passwd)
        if private_file:
            self.variable_manager.set_host_variable(h, 'ansible_ssh_private_key_file', private_file)

    def run(self):
        play = PlaybookExecutor(
            playbooks=self.playbooks,
            passwords=self.passwords,
            inventory=self.inventory,
            loader=self.loader,
            variable_manager=self.variable_manager,
            options=self.options
        )
        # play._tqm._stdout_callback = CallbackModule()
        play._tqm._stdout_callback = ResultCallback(track_id=self.track_id)
        return play.run()

    def add_playbook_vars(self, key, value):
        extra_vars = self.variable_manager.extra_vars
        extra_vars[key] = value
        self.variable_manager.extra_vars = extra_vars

    def get_playbook_vars(self):

        self.variable_manager.get_vars(play=self.playbooks)
