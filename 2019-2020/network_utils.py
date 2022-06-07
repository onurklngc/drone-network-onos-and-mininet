def host_ip_to_mac(ip):
    if ip.split(".")[-2] == "0":
        # Regular host
        host_id = ip.split(".")[-1]
        mac = "00:00:00:00:00:1" + hex(int(host_id)).split('x')[-1].zfill(1)
    else:
        # Switch dummy host which is temporary content server
        host_id = ip.split(".")[-2]
        mac = '00:00:00:00:%s:00' % hex(int(host_id)).split('x')[-1].zfill(2)
    return mac


def host_id_to_ip(host_id):
    host_ip = "10.0.0.%s" % host_id
    return host_ip


def host_ip_to_id(host_ip):
    host_id = host_ip.split(".")[-1]
    return int(host_id)


def host_ip_to_its_one_by_one_switch_id(host_ip):
    host_id = host_ip.split(".")[-1]
    return int(host_id) - 1


def switch_id_to_its_cache_host_ip(switch_id):
    switch_id = int(switch_id.split(":")[1], 16)
    cache_host_ip = "10.0.%s.1" % switch_id
    return cache_host_ip


def server_ip_to_mac(ip):
    # Switch dummy host which is temporary content server
    host_id = ip.split(".")[-2]
    mac = '00:00:00:00:%s:00' % hex(int(host_id)).split('x')[-1].zfill(2)
    return mac
