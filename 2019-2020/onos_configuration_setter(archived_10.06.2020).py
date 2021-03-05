import json

import requests

# ONOS_ADDRESS = "http://192.168.31.176:8181"
onos_address = "http://localhost:8181"
configuration_path = "/onos/v1/configuration/"
application_path = "/onos/v1/applications/"

applications_to_activate = ["org.onosproject.openflow",
                            "org.onosproject.fwd",
                            "org.onosproject.cpman",
                            # "org.onosproject.mobility"
                            ]

payloads = {
    "org.onosproject.provider.lldp.impl.LldpLinkProvider": {
        "probeRate": "10000",
        "maxDiscoveryDelayMs": "9000",
        "enabled": "true",
        "useBddp": "true",
        "useStaleLinkAge": "true",
        "staleLinkAge": "30000"
    },
    "org.onosproject.fwd.ReactiveForwarding": {
        "matchIpv6Address": "false",
        "matchIpv6FlowLabel": "false",
        "ignoreIPv4Multicast": "false",
        "matchIcmpFields": "false",
        "flowTimeout": "15",
        "matchTcpUdpPorts": "false",
        "recordMetrics": "false",
        "matchDstMacOnly": "false",
        "matchIpv4Address": "false",
        "matchVlanId": "false",
        "matchIpv4Dscp": "false",
        "ipv6Forwarding": "false",
        "packetOutOfppTable": "false",
        "packetOutOnly": "false",
        "flowPriority": "10"
    }
    ,
    "org.onosproject.core.impl.CoreManager": {
        "maxEventTimeLimit": "2000",
        "sharedThreadPerformanceCheck": "true",
        "sharedThreadPoolSize": "30"
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
    for parameter, payload in payloads.iteritems():
        response = requests.request("POST", onos_address + configuration_path + parameter, data=json.dumps(payload),
                                    headers=headers)
        print(response.text)


if __name__ == '__main__':
    activate_applications()
    change_configurations()
    print("Completed.")
