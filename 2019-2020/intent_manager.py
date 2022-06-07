import traceback

from network_utils import host_ip_to_mac
from switch_manager import SwitchManager
import controller_utils

DEBUG = True


def debug(msg):
    if DEBUG:
        print(msg)


def generate_intent_key(h1_ip, h2_ip):
    return h1_ip + "-" + h2_ip if h1_ip < h2_ip else h2_ip + "-" + h1_ip


def generate_intent_definition(h1_ip, h2_ip):
    mac1 = host_ip_to_mac(h1_ip)
    mac2 = host_ip_to_mac(h2_ip)
    key = generate_intent_key(h1_ip, h2_ip)
    payload = {
        "type": "HostToHostIntent",
        "appId": "org.onosproject.ovsdb",
        "priority": 55,
        "one": mac1 + "/None",
        "two": mac2 + "/None",
        "key": key
    }
    return payload


class IntentManager(object):
    switch_manager = None

    number_of_active_intents = 0
    number_of_deleted_intents = 0

    def __init__(self, switch_manager=None):
        if switch_manager:
            self.switch_manager = switch_manager
        else:
            self.switch_manager = SwitchManager()

    def create_host_2_host_intent(self, h1_ip, h2_ip):
        try:
            payload = generate_intent_definition(h1_ip, h2_ip)
            debug(payload)
            controller_utils.post_intent(payload)
            self.number_of_active_intents += 1
        except Exception as e:
            print(traceback.format_exc())
            print (e)

        debug("Number of active intents: %d" % self.number_of_active_intents)

    def delete_host_2_host_intent(self, h1_ip, h2_ip):
        try:
            key = generate_intent_key(h1_ip, h2_ip)
            controller_utils.delete_intent(key)
            self.number_of_deleted_intents += 1
        except Exception as e:
            print(traceback.format_exc())
            print (e)
        debug("Number of deleted intents: %d" % self.number_of_deleted_intents)

    def delete_host_2_host_intent_by_key(self, key):
        try:
            controller_utils.delete_intent(key)
            self.number_of_deleted_intents += 1
        except Exception as e:
            print(traceback.format_exc())
            print (e)
        debug("Number of deleted intents: %d" % self.number_of_deleted_intents)


if __name__ == '__main__':
    link_manager = IntentManager()
    # link_manager.create_host_2_host_intent("10.0.0.1", "10.0.5.1")
    link_manager.create_host_2_host_intent("10.0.0.1", "10.0.0.3")
    # link_manager.delete_host_2_host_intent("10.0.0.1", "10.0.0.2")
    # link_manager.delete_host_2_host_intent("10.0.0.1", "10.0.5.1")
    # link_manager.create_host_2_host_intent("10.0.0.3", "10.0.9.1")
    # link_manager.delete_host_2_host_intent("10.0.0.3", "10.0.9.1")
    # link_manager.delete_host_2_host_intent_by_key("10.0.0.3-10.0.1.9")

