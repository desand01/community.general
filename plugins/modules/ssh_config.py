#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2015, Björn Andersson
# Copyright (c) 2021, Ansible Project
# Copyright (c) 2021, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: ssh_config
short_description: Manage SSH config for user
version_added: '2.0.0'
description:
  - Configures SSH hosts with special C(IdentityFile)s and hostnames.
author:
  - Björn Andersson (@gaqzi)
  - Abhijeet Kasurde (@Akasurde)
extends_documentation_fragment:
  - community.general.attributes
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  state:
    description:
      - Whether a host entry should exist or not.
    default: present
    choices: ['present', 'absent']
    type: str
  user:
    description:
      - Which user account this configuration file belongs to.
      - If none given and O(ssh_config_file) is not specified, C(/etc/ssh/ssh_config) is used.
      - If a user is given, C(~/.ssh/config) is used.
      - Mutually exclusive with O(ssh_config_file).
    type: str
  group:
    description:
      - Which group this configuration file belongs to.
      - If none given, O(user) is used.
    type: str
  host:
    description:
      - The endpoint this configuration is valid for.
      - It can be an actual address on the internet or an alias that connects to the value of O(hostname).
    required: true
    type: str
  hostname:
    description:
      - The actual host to connect to when connecting to the host defined.
    type: str
  port:
    description:
      - The actual port to connect to when connecting to the host defined.
    type: str
  remote_user:
    description:
      - Specifies the user to log in as.
    type: str
  identity_file:
    description:
      - The path to an identity file (SSH private key) that is used when connecting to this host.
      - File need to exist and have mode V(0600) to be valid.
    type: path
  identities_only:
    description:
      - Specifies that SSH should only use the configured authentication identity and certificate files (either the default
        files, or those explicitly configured in the C(ssh_config) files or passed on the ssh command-line), even if C(ssh-agent)
        or a C(PKCS11Provider) or C(SecurityKeyProvider) offers more identities.
    type: bool
    version_added: 8.2.0
  user_known_hosts_file:
    description:
      - Sets the user known hosts file option.
    type: str
  strict_host_key_checking:
    description:
      - Whether to strictly check the host key when doing connections to the remote host.
      - The value V(accept-new) is supported since community.general 8.6.0.
    choices: ['yes', 'no', 'ask', 'accept-new']
    type: str
  proxycommand:
    description:
      - Sets the C(ProxyCommand) option.
      - Mutually exclusive with O(proxyjump).
    type: str
  proxyjump:
    description:
      - Sets the C(ProxyJump) option.
      - Mutually exclusive with O(proxycommand).
    type: str
    version_added: 6.5.0
  forward_agent:
    description:
      - Sets the C(ForwardAgent) option.
    type: bool
    version_added: 4.0.0
  add_keys_to_agent:
    description:
      - Sets the C(AddKeysToAgent) option.
    type: bool
    version_added: 8.2.0
  ssh_config_file:
    description:
      - SSH config file.
      - If O(user) and this option are not specified, C(/etc/ssh/ssh_config) is used.
      - Mutually exclusive with O(user).
    type: path
  host_key_algorithms:
    description:
      - Sets the C(HostKeyAlgorithms) option.
    type: str
    version_added: 6.1.0
  controlmaster:
    description:
      - Sets the C(ControlMaster) option.
    choices: ['yes', 'no', 'ask', 'auto', 'autoask']
    type: str
    version_added: 8.1.0
  controlpath:
    description:
      - Sets the C(ControlPath) option.
    type: str
    version_added: 8.1.0
  controlpersist:
    description:
      - Sets the C(ControlPersist) option.
    type: str
    version_added: 8.1.0
  dynamicforward:
    description:
      - Sets the C(DynamicForward) option.
    type: str
    version_added: 10.1.0
  other_options:
    description:
      - Allows specifying arbitrary SSH config entry options using a dictionary.
      - The key names must be lower case. Keys with upper case values are rejected.
      - The values must be strings. Other values are rejected.
    type: dict
    version_added: 10.4.0
requirements:
  - paramiko
"""

EXAMPLES = r"""
- name: Add a host in the configuration
  community.general.ssh_config:
    user: akasurde
    host: "example.com"
    hostname: "github.com"
    identity_file: "/home/akasurde/.ssh/id_rsa"
    port: '2223'
    state: present
    other_options:
      serveraliveinterval: '30'

- name: Add SSH config with key auto-added to agent
  community.general.ssh_config:
    user: devops
    host: "example.com"
    hostname: "staging.example.com"
    identity_file: "/home/devops/.ssh/id_rsa"
    add_keys_to_agent: true
    state: present

- name: Delete a host from the configuration
  community.general.ssh_config:
    ssh_config_file: "{{ ssh_config_test }}"
    host: "example.com"
    state: absent
"""

RETURN = r"""
hosts_added:
  description: A list of host added.
  returned: success
  type: list
  sample: ["example.com"]
hosts_removed:
  description: A list of host removed.
  returned: success
  type: list
  sample: ["example.com"]
hosts_changed:
  description: A list of host changed.
  returned: success
  type: list
  sample: ["example.com"]
hosts_change_diff:
  description: A list of host diff changes.
  returned: on change
  type: list
  sample:
    [
      {
        "example.com": {
          "new": {
            "hostname": "github.com",
            "identityfile": [
              "/tmp/test_ssh_config/fake_id_rsa"
            ],
            "port": "2224"
          },
          "old": {
            "hostname": "github.com",
            "identityfile": [
              "/tmp/test_ssh_config/fake_id_rsa"
            ],
            "port": "2224"
          }
        }
      }
    ]
"""

import os

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.six import string_types
from ansible_collections.community.general.plugins.module_utils._stormssh import ConfigParser, HAS_PARAMIKO, PARAMIKO_IMPORT_ERROR
from ansible_collections.community.general.plugins.module_utils.ssh import determine_config_file


def convert_bool(value):
    if value is True:
        return 'yes'
    if value is False:
        return 'no'
    return None


def fix_bool_str(value):
    if value == 'True':
        return 'yes'
    if value == 'False':
        return 'no'
    return value


class SSHConfig(object):
    def __init__(self, module):
        self.module = module
        if not HAS_PARAMIKO:
            module.fail_json(msg=missing_required_lib('PARAMIKO'), exception=PARAMIKO_IMPORT_ERROR)
        self.params = module.params
        self.user = self.params.get('user')
        self.group = self.params.get('group') or self.user
        self.host = self.params.get('host')
        self.config_file = self.params.get('ssh_config_file')
        self.identity_file = self.params['identity_file']
        self.check_ssh_config_path()
        try:
            self.config = ConfigParser(self.config_file)
        except FileNotFoundError:
            self.module.fail_json(msg="Failed to find %s" % self.config_file)
        self.config.load()

    def check_ssh_config_path(self):
        self.config_file = determine_config_file(self.user, self.config_file)

        # See if the identity file exists or not, relative to the config file
        if os.path.exists(self.config_file) and self.identity_file is not None:
            dirname = os.path.dirname(self.config_file)
            self.identity_file = os.path.join(dirname, self.identity_file)

            if not os.path.exists(self.identity_file):
                self.module.fail_json(msg='IdentityFile %s does not exist' % self.params['identity_file'])

    def ensure_state(self):
        hosts_result = self.config.search_host(self.host)
        state = self.params['state']
        args = dict(
            hostname=self.params.get('hostname'),
            port=self.params.get('port'),
            identity_file=self.params.get('identity_file'),
            identities_only=convert_bool(self.params.get('identities_only')),
            user=self.params.get('remote_user'),
            strict_host_key_checking=self.params.get('strict_host_key_checking'),
            user_known_hosts_file=self.params.get('user_known_hosts_file'),
            proxycommand=self.params.get('proxycommand'),
            proxyjump=self.params.get('proxyjump'),
            host_key_algorithms=self.params.get('host_key_algorithms'),
            forward_agent=convert_bool(self.params.get('forward_agent')),
            add_keys_to_agent=convert_bool(self.params.get('add_keys_to_agent')),
            controlmaster=self.params.get('controlmaster'),
            controlpath=self.params.get('controlpath'),
            controlpersist=fix_bool_str(self.params.get('controlpersist')),
            dynamicforward=self.params.get('dynamicforward'),
        )
        if self.params.get('other_options'):
            for key, value in self.params.get('other_options').items():
                if key.lower() != key:
                    self.module.fail_json(msg="The other_options key {key!r} must be lower case".format(key=key))
                if key not in args:
                    if not isinstance(value, string_types):
                        self.module.fail_json(msg="The other_options value provided for key {key!r} must be a string, got {type}".format(key=key,
                                                                                                                                         type=type(value)))
                    args[key] = value
                else:
                    self.module.fail_json(msg="Multiple values provided for key {key!r}".format(key=key))

        config_changed = False
        hosts_changed = []
        hosts_change_diff = []
        hosts_removed = []
        hosts_added = []

        hosts_result = [host for host in hosts_result if host['host'] == self.host]

        if hosts_result:
            for host in hosts_result:
                if state == 'absent':
                    # Delete host from the configuration
                    config_changed = True
                    hosts_removed.append(host['host'])
                    self.config.delete_host(host['host'])
                else:
                    # Update host in the configuration
                    changed, options = self.change_host(host['options'], **args)

                    if changed:
                        config_changed = True
                        self.config.update_host(host['host'], options)
                        hosts_changed.append(host['host'])
                        hosts_change_diff.append({
                            host['host']: {
                                'old': host['options'],
                                'new': options,
                            }
                        })
        elif state == 'present':
            changed, options = self.change_host(dict(), **args)

            if changed:
                config_changed = True
                hosts_added.append(self.host)
                self.config.add_host(self.host, options)

        if config_changed and not self.module.check_mode:
            try:
                self.config.write_to_ssh_config()
            except PermissionError as perm_exec:
                self.module.fail_json(
                    msg="Failed to write to %s due to permission issue: %s" % (self.config_file, to_native(perm_exec)))
            # Make sure we set the permission
            perm_mode = '0600'
            if self.config_file == '/etc/ssh/ssh_config':
                perm_mode = '0644'
            self.module.set_mode_if_different(self.config_file, perm_mode, False)
            # Make sure the file is owned by the right user and group
            self.module.set_owner_if_different(self.config_file, self.user, False)
            self.module.set_group_if_different(self.config_file, self.group, False)

        self.module.exit_json(changed=config_changed,
                              hosts_changed=hosts_changed,
                              hosts_removed=hosts_removed,
                              hosts_change_diff=hosts_change_diff,
                              hosts_added=hosts_added)

    @staticmethod
    def change_host(options, **kwargs):
        options = deepcopy(options)
        changed = False
        for k, v in kwargs.items():
            if '_' in k:
                k = k.replace('_', '')

            if not v:
                if options.get(k):
                    del options[k]
                    changed = True
            elif options.get(k) != v and not (isinstance(options.get(k), list) and v in options.get(k)):
                options[k] = v
                changed = True

        return changed, options


def main():
    module = AnsibleModule(
        argument_spec=dict(
            group=dict(default=None, type='str'),
            host=dict(type='str', required=True),
            hostname=dict(type='str'),
            host_key_algorithms=dict(type='str', no_log=False),
            identity_file=dict(type='path'),
            identities_only=dict(type='bool'),
            other_options=dict(type='dict'),
            port=dict(type='str'),
            proxycommand=dict(type='str', default=None),
            proxyjump=dict(type='str', default=None),
            forward_agent=dict(type='bool'),
            add_keys_to_agent=dict(type='bool'),
            remote_user=dict(type='str'),
            ssh_config_file=dict(default=None, type='path'),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            strict_host_key_checking=dict(
                type='str',
                default=None,
                choices=['yes', 'no', 'ask', 'accept-new'],
            ),
            controlmaster=dict(type='str', default=None, choices=['yes', 'no', 'ask', 'auto', 'autoask']),
            controlpath=dict(type='str', default=None),
            controlpersist=dict(type='str', default=None),
            dynamicforward=dict(type='str'),
            user=dict(default=None, type='str'),
            user_known_hosts_file=dict(type='str', default=None),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ['user', 'ssh_config_file'],
            ['proxycommand', 'proxyjump'],
        ],
    )

    ssh_config_obj = SSHConfig(module)
    ssh_config_obj.ensure_state()


if __name__ == '__main__':
    main()
