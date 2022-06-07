import json

import requests

ACTIVATE_APPS = True
# ONOS_ADDRESS = "http://192.168.31.176:8181"
onos_address = "http://localhost:8181"
configuration_path = "/onos/v1/configuration/"
network_configuration_path = "/onos/v1/network/configuration/"
application_path = "/onos/v1/applications/"

applications_to_activate = [
    "org.onosproject.openflow-base",
    "org.onosproject.hostprovider",
    "org.onosproject.netcfglinksprovider",
    # "org.onosproject.fwd"
    # "org.onosproject.proxyarp"

]

configurations = {
    "org.onosproject.fwd.ReactiveForwarding": {
        "flowTimeout": "999",
    },
}

network_configurations = {
    "apps": {
        "org.onosproject.core": {
            "core": {
                "linkDiscoveryMode": "STRICT"
            }
        },
        "org.onosproject.netcfglinksprovider": {
        }
    }
}

headers = {
    'Authorization': "Basic b25vczpyb2Nrcw==",
}


# Activate apps first
def activate_applications():
    for application in applications_to_activate:
        response = requests.request("POST", "{}{}{}/active".format(onos_address, application_path, application),
                                    headers=headers)
        print("ACTIVATE %s result: %s" % (application, response.status_code))


def change_onos_configurations():
    for parameter, payload in configurations.items():
        response = requests.request("POST", onos_address + configuration_path + parameter, data=json.dumps(payload),
                                    headers=headers)
        print("UPLOAD config for %s result: %s" % (parameter, response.status_code))


def change_app_configurations():
    for parameter, payload in network_configurations.items():
        response = requests.request("POST", onos_address + network_configuration_path + parameter,
                                    data=json.dumps(payload),
                                    headers=headers)
        print("UPLOAD network config for %s result: %s" % (parameter, response.status_code))


if __name__ == '__main__':
    if ACTIVATE_APPS:
        activate_applications()
    change_onos_configurations()
    change_app_configurations()
