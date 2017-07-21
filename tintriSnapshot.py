#!/usr/bin/python

# (c) 2017, Adam Cavaliere <acavaliere@tintri.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import time

try:
	from tintri.v310 import Tintri
	from tintri.v310 import VirtualMachineFilterSpec
	TINTRI_AVAILABLE = True
except ImportError:
	TINTRI_AVAILABLE = False

ANSIBLE_METADATA = {'status': ['preview'],
					'supported_by': 'community',
					'metadata_version': '1.0'}
	
DOCUMENTATION = '''
---
module: tintriSnapshot
version_added: "1.0"
author: "Adam Cavaliere (@AdamCavaliere)"
short_description: Take Snapshots of VMs on Tintri
description:
- A module to control Philips Hue lights via the python-hue library.
requirements:
- Tintri_PySDK-1.0-py2-none-any.whl
options:
  tgc:
	required: true
	description:
	- "The instance of Tintri Global Center that has the VMs"
  username:
	required: true
	description:
	- "User Executing the snapshot"
  password:
	required: true
	description:
	- "The password of the username executing the snapshot"
  retentionMinutes:
	required: false
	description:
	- "Time in minutes that the snapshot should be retained for"
  VM:
	required: true
	description:
	- "The name of the VM to be snapshotted"
  snapDescription:
	required: false
	description:
	- "The description given for the snapshot. If not provided, a standard description will be given"
  snapConsistency:
	required: false
	description:
	- "CRASH_CONSISTENT | VM_CONSISTENT | APP_CONSISTENT"
	- "Default is CRASH_CONSISTENT"
'''

EXAMPLES = '''
# Snapshot VMs
- tintriSnapshot:
	tgc: tintriGlobalCenter.tintri.com
	username: foo
	password: bar
	snapDescription: Example Snapshot
	retentionMinutes: 120
	VM: [vms]
	

'''

def CreateSession(user,passw,vmstore):
		session = Tintri(vmstore)
		session.login(user,passw)
		if session.is_logged_in():
			return session
		else:
			return False

def GetVMStore(VM_Name,username,password,tgc):
		tgcSession = CreateSession(username,password,tgc)
		VM_filter = VirtualMachineFilterSpec()
		VM_filter.name = VM_Name
		VM_filter.live = "true"
		single_vm = tgcSession.get_vms(filters = VM_filter)
		tgcSession.logout()
		return single_vm[0].vmstoreName
		
def GetVMUUID(session,VM_Name):
	VM_filter = VirtualMachineFilterSpec()
	VM_filter.name = VM_Name
	VM_filter.live = "true"
	single_vm = session.get_vms(filters = VM_filter)
	if (single_vm):
		return single_vm[0].uuid.uuid
	else:
		return False


def main():

	module = AnsibleModule(
		argument_spec = dict(
			VM=dict(required=True, type='str'),
			tgc=dict(required=True, type='str'),
			username=dict(required=True, type='str'),
			password=dict(required=True,type='str'),
			retentionMinutes=dict(default=1440,type='int'),
			snapDescription=dict(default='Ansible Snapshot',type='str'),
			snapConsistency=dict(default='CRASH_CONSISTENT',type='str')
		),
		supports_check_mode=False
	)

	

	if not TINTRI_AVAILABLE:
		module.fail_json(msg="The Tintri sdk is not installed")

	# Connect to Tintri Global Center
	try:
		VMStore = GetVMStore(module.params['VM'],module.params['username'],module.params['password'],module.params['tgc'])
	except Exception, e:
		module.fail_json(msg="Failed to connect to Tintri Global Center. Error was: %s" % str(e))
		
	VMStoreSession = CreateSession(module.params['username'],module.params['password'],VMStore)
	VMUUID = GetVMUUID(VMStoreSession,module.params['VM'])
	SnapshotSpec = {
					"typeId": "com.tintri.api.rest.v310.dto.domain.beans.snapshot.SnapshotSpec",
					"consistency": module.params['snapConsistency'],
					"replicaRetentionMinutes": module.params['retentionMinutes'],
					"retentionMinutes": module.params['retentionMinutes'],
					"snapshotName": module.params['snapDescription'],
					"sourceVmTintriUUID": VMUUID,
	}	
	try:
		VMStoreSession.create_snapshot(SnapshotSpec)
	except:
		module.fail_json(msg="The snapshot could not be created")

	module.exit_json(changed=True)
# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
	main()
