import requests

from network_utils import host_ip_to_mac
from settings import CONTROLLER_IP
import json

DEBUG = True


def debug(msg):
    if DEBUG:
        print(msg)


def escape_path(path):
    return path.replace(":", "%3A").replace("/", "%2F")


class SwitchManager(object):
    switch_name_to_formal_name = {}
    switch_id_to_of_name = {}
    switch_of_name_to_id = {}

    def get_of_name_by_name(self, switch_name):
        if switch_name in self.switch_name_to_formal_name:
            return self.switch_name_to_formal_name[switch_name]
        else:
            formal_switch_name = "of:" + hex(int(switch_name[1:])).split('x')[-1].zfill(16)
            self.switch_name_to_formal_name[switch_name] = formal_switch_name
            return formal_switch_name

    def get_id_by_of_name(self, switch_name):
        if switch_name not in self.switch_of_name_to_id:
            switch_id = int(switch_name.split(":")[1], 16) - 1
            self.switch_id_to_of_name[switch_id] = switch_name
            self.switch_of_name_to_id[switch_name] = switch_id
        else:
            switch_id = self.switch_of_name_to_id[switch_name]
        return switch_id

    def get_of_name_by_id(self, switch_id):
        if switch_id in self.switch_id_to_of_name:
            return self.switch_id_to_of_name[switch_id]
        else:
            switch_name = "of:" + hex(int(switch_id + 1)).split('x')[-1].zfill(16)
            self.switch_id_to_of_name[switch_id] = switch_name
            return switch_name


if __name__ == '__main__':
    switch_manager = SwitchManager()
