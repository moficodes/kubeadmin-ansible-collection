#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.moficodes.kubeadmin.plugins.module_utils.ibmcloud import cluster_create

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: kubeadmin_cluster_create
short_description: Configure IBM Cloud KubeAdmin 'kubeadmin_cluster_create' resource

version_added: "2.8"

description:
    - Create an IBM Cloud Kubernetes Cluster Resource
    - This module supports idempotency

options:
    public_vlan_id:
        description:
            - Public VLAN ID
        required: False
        type: str
    default_pool_size:
        description:
            - The size of the default worker pool
        required: False
        type: int
        default: 1
    private_vlan_id:
        description:
            - Private VLAN ID
        required: False
        type: str
    entitlement:
        description:
            - Entitlement option reduces additional OCP Licence cost in Openshift Clusters
        required: False
        type: str
    gateway_enabled:
        description:
            - Set true for gateway enabled clusters
        required: False
        type: bool
        default: False
    name:
        description:
            - (Required for new resource) The cluster name
        required: True
        type: str
    no_subnet:
        description:
            - Boolean value set to true when subnet creation is not required.
        required: False
        type: bool
        default: False
    master_version:
        description:
            - Kubernetes version of Master node
        required: True
        type: str
    machine_type:
        description:
            - Machine type
        required: True
        type: str
    subnet_id:
        description:
            - List of subnet IDs
        required: False
        type: list
        elements: str
    datacenter:
        description:
            - (Required for new resource) The datacenter where this cluster will be deployed
        required: True
        type: str
    disk_encryption:
        description:
            - disc encryption done, if set to true.
        required: False
        type: bool
        default: True
    hardware:
        description:
            - (Required for new resource) Hardware type
        required: True
        type: str
    tags:
        description:
            - comma separated tags values for the cluster resource
        required: False
        type: str
    ibmcloud_api_key:
        description:
            - The IBM Cloud API key to authenticate with the IBM Cloud
              platform. This can also be provided via the environment
              variable 'IBMCLOUD_API_KEY'.
        required: True

author:
    - Mofi Rahman (@moficodes)
'''


def run_module():

    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        resource_group=dict(
            required=True,
            type='str'),
        public_vlan_id=dict(
            required=False,
            default="",
            type='str'),
        default_pool_size=dict(
            required=False,
            default=1,
            type='int'),
        private_vlan_id=dict(
            required=False,
            default="",
            type='str'),
        entitlement=dict(
            required=False,
            default="",
            type='str'),
        name=dict(
            required=True,
            type='str'),
        machine_type=dict(
            required=True,
            type='str'),
        datacenter=dict(
            required=True,
            type='str'),
        master_version=dict(
            required=True,
            type='str'),
        tags=dict(
            required=False,
            default="",
            type='str'),
        ibmcloud_api_key=dict(
            type='str',
            no_log=True,
            fallback=(env_fallback, ['IC_API_KEY']),
            required=True)
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    if module.check_mode:
        module.exit_json(**result)

    if module.params['name'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)
    try:
        result_ds = cluster_create(
            module.params['ibmcloud_api_key'], 
            module.params['resource_group'], 
            module.params['datacenter'],
            module.params['entitlement'], 
            module.params['machine_type'],
            module.params['master_version'], 
            module.params['name'], 
            module.params['private_vlan_id'], 
            module.params['public_vlan_id'],
            module.params['default_pool_size'],
            module.params['tags']
            )
        print(result_ds)
        result['data'] = result_ds
        result['changed'] = True
    except Exception as e:
        module.fail_json(msg=e.args, **result)
        print(e)
    
    module.exit_json(**result)

# cluster_create(api_key, resource_group, datacenter, entitlement, machine_type, master_version, name, private_vlan,public_vlan, worker_num):
def main():
    run_module()


if __name__ == '__main__':
    main()
