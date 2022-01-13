import json
import logging

import requests

from network_utils import host_ip_to_mac
from settings import CONTROLLER_IP, LOG_LEVEL

LINK_CONFIGURATION_PATH = "/onos/v1/network/configuration/links/"
NETWORK_CONFIGURATION_PATH = "/onos/v1/network/configuration"
DISTANCE_ESTIMATION_PATH = "/onos/v1/paths/{}/{}"
INTENTS_PATH = "/onos/v1/intents"
METRICS_PATH = "/onos/cpman/controlmetrics/messages"
HOSTS_PATH = "/onos/v1/hosts"
URL_TEMPLATE = "http://{}:8181{}"

LINK_CONFIGURATION_URL = URL_TEMPLATE.format(CONTROLLER_IP, LINK_CONFIGURATION_PATH)
NETWORK_CONFIGURATION_URL = URL_TEMPLATE.format(CONTROLLER_IP, NETWORK_CONFIGURATION_PATH)
DISTANCE_ESTIMATION_URL = URL_TEMPLATE.format(CONTROLLER_IP, DISTANCE_ESTIMATION_PATH)
INTENTS_URL = URL_TEMPLATE.format(CONTROLLER_IP, INTENTS_PATH)
METRICS_URL = URL_TEMPLATE.format(CONTROLLER_IP, METRICS_PATH)
HOSTS_URL = URL_TEMPLATE.format(CONTROLLER_IP, HOSTS_PATH)

BASIC_AUTH_HEADERS = {
    'Authorization': "Basic b25vczpyb2Nrcw==",
}
s = requests.Session()
s.auth = ('onos', 'rocks')

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")


def escape_path(path):
    return path.replace(":", "%3A").replace("/", "%2F")


def get_distance_and_switches_passed(src, dst):
    switches_passed = []

    if src.startswith("of"):  # Source is switch
        # src_id = urllib2.quote('of:0000000000000001')
        src_id = escape_path(src)
    else:
        src_mac = host_ip_to_mac(src)
        src_id = escape_path(src_mac) + '%2FNone'

    dst_mac = host_ip_to_mac(dst)
    dst_id = escape_path(dst_mac) + '%2FNone'
    link = DISTANCE_ESTIMATION_URL.format(src_id, dst_id)
    response = s.request("GET", link)
    data = json.loads(response.text)["paths"][0]
    distance = data["cost"]
    for hop in data["links"]:
        if "device" in hop["dst"]:
            next_node = hop["dst"]["device"]
            switches_passed.append(next_node)
    return distance, switches_passed


def get_distance(src_of_name, dst_of_name):
    try:
        link = DISTANCE_ESTIMATION_URL.format(src_of_name, dst_of_name)
        response = s.request("GET", link)
        data = json.loads(response.text)
        if "paths" not in data or len(data["paths"]) == 0:
            return
        data = data["paths"][0]
        distance = int(data["cost"])
    except Exception as e:
        logging.error(e)
        return
    return distance


def delete_link(link):
    url = LINK_CONFIGURATION_URL + escape_path(link)
    response = s.request("DELETE", url)
    logging.debug("RESPONSE delete_link: %s" % response)


def delete_all_links():
    response = s.request("DELETE", LINK_CONFIGURATION_URL)
    logging.info("RESPONSE delete_all_links: %s" % response)


def post_link(payload):
    response = s.request("POST", LINK_CONFIGURATION_URL, data=json.dumps(payload))
    logging.debug(response.text)


def get_network_configurations():
    response = s.request("GET", NETWORK_CONFIGURATION_URL)
    current_info = json.loads(response.text)
    return current_info


def post_network_configurations(payload):
    response = s.request("POST", NETWORK_CONFIGURATION_URL, data=json.dumps(payload))
    logging.debug("RESPONSE post_network_configurations: %s" % response)


def get_intents():
    response = s.request("GET", INTENTS_URL)
    current_info = json.loads(response.text)
    return current_info


def post_intent(intent):
    logging.debug(s.request("POST", INTENTS_URL, data=json.dumps(intent)))


def delete_intent(intent_key):
    url = "{}/org.onosproject.ovsdb/{}".format(INTENTS_URL, intent_key)
    logging.debug(s.request("DELETE", url))


def get_metrics():
    response = s.request("GET", METRICS_URL)
    current_info = json.loads(response.text)
    return current_info


def post_host_location(host_ip, host_mac, switch_element_id, vlan="None", port=1, friendly_name=None):
    payload = {
        "id": f"{host_mac}/{vlan}",
        "mac": host_mac,
        "vlan": vlan,
        "suspended": False,
        "ipAddresses": [
            host_ip
        ],
        "locations": [
            {
                "elementId": switch_element_id,
                "port": str(port)
            }
        ],
    }
    if friendly_name:
        payload["annotations"] = {"name": friendly_name}

    response = s.request("POST", HOSTS_URL, data=json.dumps(payload))
    logging.debug("RESPONSE post_host_location: %s" % response)


def delete_host_location(host_mac, vlan="None"):
    host_mac_escaped = escape_path(host_mac)
    link = f"{HOSTS_URL}/{host_mac_escaped}/{vlan}"

    response = s.request("DELETE", link)
    logging.debug("RESPONSE delete_host_location: %s" % response)


if __name__ == '__main__':
    # logging.info(get_network_configurations())
    # logging.info(get_distance_and_switches_passed("of:1000000000000002", "10.0.0.3"))
    delete_all_links()
