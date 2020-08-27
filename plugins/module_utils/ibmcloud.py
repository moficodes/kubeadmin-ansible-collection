import requests
import json
import time

protocol = "https://"
subdomain_iam = "iam."
subdomain_accounts = "accounts."
subdomain_resource_controller = "resource-controller."
subdomain_clusters = "containers."
subdomain_tags = "tags.global-search-tagging."
api = "cloud.ibm.com"
identity_endpoint = protocol + subdomain_iam + \
    api + "/identity/.well-known/openid-configuration"
accounts_endpoint = protocol + subdomain_accounts + api + "/coe/v2/accounts"
resources_endpoint = protocol + subdomain_resource_controller + \
    api + "/v2/resource_instances"
resource_keys_kndpoint = protocol + \
    subdomain_resource_controller + api + "/v2/resource_keys"
containers_endpoint = protocol + subdomain_clusters + api + "/global/v1"

tag_endpoint = protocol + subdomain_tags + api + "/v3/tags"
resource_endoint = protocol + subdomain_resource_controller + \
    api + "/v1/resource_groups"

cluster_endpoint = containers_endpoint + "/clusters"
version_endpoint = containers_endpoint + "/versions"
location_endpoint = containers_endpoint + "/locations"
zones_endpoint = containers_endpoint + "/zones"
datacenters_endpoint = containers_endpoint + "/datacenters"

passcode_grant_type = "urn:ibm:params:oauth:grant-type:passcode"
apikey_grant_type = "urn:ibm:params:oauth:grant-type:apikey"
refresh_token_grant_type = "refresh_token"
basic_auth = "Basic Yng6Yng="


def get_endpoints():
    r = requests.get(identity_endpoint)
    if r.status_code != 200:
        raise Exception("did not get response")
    return r.json()


def iam_authenticate(api_key):
    endpoints = get_endpoints()
    token_endpoint = endpoints["token_endpoint"]
    headers = {"Authorization": basic_auth}
    payload = {"grant_type": apikey_grant_type, "apikey": api_key}

    r = requests.post(token_endpoint, headers=headers, params=payload)
    if r.status_code != 200:
        raise Exception("unauthorized")
    return r.json()


def get_cluster(id_or_name, resource_group, access_token):
    headers = {"Authorization": "Bearer " + access_token, "X-Auth-Resource-Group": resource_group}
    r = requests.get(cluster_endpoint+"/"+id_or_name, headers=headers)
    if r.status_code == 404:
        raise Exception("cluster not found")
    return r.json()


def cluster_ready(cluster):
    if cluster["state"] != "normal":
        return False
    if cluster["ingressHostname"] == "":
        return False
    if cluster["ingressSecretName"] == "":
        return False
    if cluster["masterState"] != "deployed":
        return False
    if cluster["masterStatus"] != "Ready":
        return False
    return True


def renew_token(refresh_token):
    endpoints = get_endpoints()
    token_endpoint = endpoints["token_endpoint"]

    headers = {"Authorization": basic_auth}
    payload = {"grant_type": refresh_token_grant_type,
               "refresh_token": refresh_token}

    r = requests.post(token_endpoint, headers=headers, params=payload)
    return r.json()


def add_tag(tag, id, resource_group, access_token):
    cluster = get_cluster(id, resource_group, access_token)
    crn = cluster["crn"]
    payload = {"tag_name": tag, "resources": [{"resource_id": crn}]}
    headers = {"Authorization": "Bearer "+access_token}
    query = {"providers": "ghost"}

    tag_url = tag_endpoint + "/attach"
    r = requests.post(tag_url, headers=headers, json=payload, params=query)
    return r.json()



def cluster_create(api_key, resource_group, datacenter, entitlement, machine_type, master_version, name, private_vlan, public_vlan, worker_num, tags):

    token = iam_authenticate(api_key)
    headers = {"Authorization": "Bearer " + token["access_token"],
            "X-Auth-Resource-Group": resource_group}
    payload = {
        "dataCenter": datacenter,
        "publicServiceEndpoint": True,
        "machineType": machine_type,
        "masterVersion": master_version,
        "name": name,
        "skitPermPrecheck": True,
        "workerNum": worker_num
    }

    if private_vlan != "" and public_vlan != "":
        payload["privateVlan"]= private_vlan
        payload["publicVlan"]= public_vlan

    if "openshift" in master_version:
        payload["defaultWorkerPoolEntitlement"]= entitlement

    # print(cluster_endpoint)
    # print(json.dumps(headers, indent=4))
    # print(json.dumps(payload, indent=4))
    already_exists= False
    created= False
    cluster_id= ""
    for _ in range(3):
        r= requests.post(cluster_endpoint, headers=headers, json=payload)
        if r.status_code == 201:
            response= r.json()
            print("cluster created name :", name)
            created= True
            cluster_id= response["id"]
            break
        if r.status_code == 409:
            print("cluster already exists")
            already_exists= True
            break
        time.sleep(5)

    if not created and not already_exists:
        raise Exception("could not create cluster")

    if already_exists:
        cluster= get_cluster(name, resource_group, token["access_token"])

        cluster_id= cluster["id"]
    
    if tags != "":
        _tags = tags.split(",")
        for tag in _tags:
            tag = tag.strip()
            add_tag(tag, cluster_id, resource_group, token["access_token"])

    tries= 200
    cluster= {}
    while tries > 0:
        token = renew_token(token["refresh_token"])
        cluster= get_cluster(cluster_id, resource_group, token["access_token"])
        # print(json.dumps(cluster, indent=4))
        ready= cluster_ready(cluster)
        if ready:
            return cluster
        print("sleeping 5 minutes before trying again")
        tries= tries - 1
        time.sleep(300)
    # if we got here, that means the cluster did not become "ready" in 3+ hours

    raise Exception("time out")


