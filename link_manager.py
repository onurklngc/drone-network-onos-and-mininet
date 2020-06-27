import traceback

from switch_manager import SwitchManager
import controller_utils

DEBUG = True


def debug(msg):
    if DEBUG:
        print(msg)


class LinkManager(object):
    switch_manager = None

    number_of_active_links = 0
    number_of_deleted_links = 0

    def __init__(self, switch_manager=None):
        if switch_manager:
            self.switch_manager = switch_manager
        else:
            self.switch_manager = SwitchManager()

    def generate_link_names(self, interface1, interface2):
        sw_interface1 = interface1.split("-eth")
        sw_interface2 = interface2.split("-eth")
        sw1 = self.switch_manager.get_of_name_by_name(sw_interface1[0])
        sw2 = self.switch_manager.get_of_name_by_name(sw_interface2[0])
        interface1 = sw_interface1[1]
        interface2 = interface2.split("eth")[1]
        link1 = "{}/{}-{}/{}".format(sw1, interface1, sw2, interface2)
        link2 = "{}/{}-{}/{}".format(sw2, interface2, sw1, interface1)
        return link1, link2

    def generate_two_way_link_payload(self, interface1, interface2):
        link1, link2 = self.generate_link_names(interface1, interface2)
        payload = {link1: {"basic": {}}, link2: {"basic": {}}}
        return payload

    def send_two_way_link_to_controller(self, interface1, interface2):
        try:
            payload = self.generate_two_way_link_payload(interface1, interface2)
            debug(payload)
            controller_utils.post_link(payload)
            self.number_of_active_links += 1
        except Exception as e:
            print(traceback.format_exc())
            print (e)

        debug("Number of active links: %d" % self.number_of_active_links)

    def delete_two_way_link_from_controller(self, interface1, interface2):
        try:
            links = self.generate_link_names(interface1, interface2)
            for link in links:
                controller_utils.delete_link(link)
            self.number_of_active_links -= 1
            self.number_of_deleted_links += 1
        except Exception as e:
            print(traceback.format_exc())
            print (e)
        debug("Number of deleted links: %d" % self.number_of_deleted_links)


if __name__ == '__main__':
    link_manager = LinkManager()
    link_manager.send_two_way_link_to_controller("s2-eth2", "s1-eth2")
    link_manager.send_two_way_link_to_controller("s2-eth3", "s3-eth2")
    # link_manager.delete_two_way_link_from_controller("s2", "s1", "s2-eth2", "s1-eth2")
