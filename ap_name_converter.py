import settings as s

def escape_path(path):
    return path.replace(":", "%3A").replace("/", "%2F")


class AccessPointNameConverter(object):
    ap_name_to_formal_name = {}
    ap_index_to_of_name = {}
    ap_of_name_to_index = {}

    def get_of_name_by_name(self, ap_name):
        if ap_name in self.ap_name_to_formal_name:
            return self.ap_name_to_formal_name[ap_name]
        else:
            ap_id = int(ap_name[len(s.AP_NAME_PREFIX):])
            formal_ap_name = "of:1" + hex(ap_id).split('x')[-1].zfill(15)
            self.ap_name_to_formal_name[ap_name] = formal_ap_name
            return formal_ap_name

    def get_id_by_of_name(self, ap_name):
        if ap_name not in self.ap_of_name_to_index:
            ap_index = int(ap_name.split(":1")[1], 16) - 1
            self.ap_index_to_of_name[ap_index] = ap_name
            self.ap_of_name_to_index[ap_name] = ap_index
        else:
            ap_index = self.ap_of_name_to_index[ap_name]
        return ap_index

    def get_of_name_by_index(self, ap_index):
        if ap_index in self.ap_index_to_of_name:
            return self.ap_index_to_of_name[ap_index]
        else:
            ap_name = "of:" + hex(int(ap_index + 1)).split('x')[-1].zfill(16)
            self.ap_index_to_of_name[ap_index] = ap_name
            return ap_name


if __name__ == '__main__':
    ap_name_converter = AccessPointNameConverter()
