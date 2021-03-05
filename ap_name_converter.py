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


class AccessPointNameConverter(object):
    ap_name_to_formal_name = {}
    ap_id_to_of_name = {}
    ap_of_name_to_id = {}

    def get_of_name_by_name(self, ap_name):
        if ap_name in self.ap_name_to_formal_name:
            return self.ap_name_to_formal_name[ap_name]
        else:
            formal_ap_name = "of:1" + hex(int(ap_name[1:])).split('x')[-1].zfill(15)
            self.ap_name_to_formal_name[ap_name] = formal_ap_name
            return formal_ap_name

    def get_id_by_of_name(self, ap_name):
        if ap_name not in self.ap_of_name_to_id:
            ap_id = int(ap_name.split(":1")[1], 16) - 1
            self.ap_id_to_of_name[ap_id] = ap_name
            self.ap_of_name_to_id[ap_name] = ap_id
        else:
            ap_id = self.ap_of_name_to_id[ap_name]
        return ap_id

    def get_of_name_by_id(self, ap_id):
        if ap_id in self.ap_id_to_of_name:
            return self.ap_id_to_of_name[ap_id]
        else:
            ap_name = "of:" + hex(int(ap_id + 1)).split('x')[-1].zfill(16)
            self.ap_id_to_of_name[ap_id] = ap_name
            return ap_name


if __name__ == '__main__':
    ap_name_converter = AccessPointNameConverter()
