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
import json
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
  poolName:
	required: false
	description:
	- "Optional to specify a specific Pool to execute. If not set, ALL"
	- "will be passed"
'''

EXAMPLES = '''
# Execute TGC Scale Out Recommendations
- tintriScaleOut:
	tgc: tintriGlobalCenter.tintri.com
	username: foo
	password: bar
	poolName: "Dev/Test Pool"
	

'''

def CreateSession(user,passw,TGC):
		session = Tintri(TGC)
		session.login(user,passw)
		if session.is_logged_in():
			return session
		else:
			return False

def getPoolIds(tgcPools):
	pools = {}
	for pool in tgcPools:
		pools[pool.name] = pool.uuid.uuid
	return pools
	
def getRecommendationIDs(recommendations):
	available_recommendations = {}
	for recommendation in recommendations:
		if ((recommendation.state == "AVAILABLE") or (recommendation.state == "AVAILABLE_ACKED")):
			#print recommendation
			available_recommendations[recommendation.id] = recommendation.vmstorePoolId
	return available_recommendations

		
def main():
	module = AnsibleModule(
		argument_spec = dict(
			tgc=dict(required=True, type='str'),
			username=dict(required=True, type='str'),
			password=dict(required=True,type='str'),
			poolName=dict(default='ALL',type='str'),
		),
		supports_check_mode=False
	)

	

	if not TINTRI_AVAILABLE:
		module.fail_json(msg="The Tintri sdk is not installed")

	# Connect to Tintri Global Center
	try:
		tgcSession = CreateSession(module.params['username'],module.params['password'],module.params['tgc'])
	except Exception, e:
		module.fail_json(msg="Failed to connect to Tintri Global Center. Error was: %s" % str(e))
	
	try:
		tgcPools = tgcSession.get_vmstore_pools()
	except:
		module.fail_json(msg="Couldn't get pool information!")
	pools = getPoolIds(tgcPools)
	
	if module.params['poolName'] != "ALL": #Checks to see if a VMstore Pool is specified
		if module.params['poolName'] in pools:
			pools[module.params['poolName']] = pools[module.params['poolName']]
		else:
			module.fail_json(msg="Couldn't match up the pool name - please check case")
	for VMstorePool in pools:
		recommendations = tgcSession.get_recommendations(pools[VMstorePool])
		current_recs = getRecommendationIDs(recommendations)
		if current_recs:
				for recommendation in current_recs:
					tgcSession.acknowledge_recommendation(current_recs[recommendation], recommendation)
					tgcSession.accept_recommendation(current_recs[recommendation],recommendation)

		
	module.exit_json(changed=True)
	
from ansible.module_utils.basic import *
if __name__ == '__main__':
	main()
