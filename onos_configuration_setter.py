import requests
import json

# onos_address = "http://192.168.31.176:8181"
onos_address = "http://localhost:8181"
network_configuration_path = "/onos/v1/network/configuration/"
application_path = "/onos/v1/applications/"

applications_to_activate = ["org.onosproject.openflow-base",
                            "org.onosproject.hostprovider",
                            "org.onosproject.netcfglinksprovider",
                            "org.onosproject.proxyarp",
                            "org.onosproject.cpman"]

network_configurations = {
    "apps": {
        "org.onosproject.core": {
            "core": {
                "linkDiscoveryMode": "STRICT"
            }
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
    print(response.text)


def change_configurations():
    for parameter, payload in network_configurations.iteritems():
        response = requests.request("POST", onos_address + network_configuration_path + parameter,
                                    data=json.dumps(payload),
                                    headers=headers)
        print(response.text)


if __name__ == '__main__':
    activate_applications()
    change_configurations()
