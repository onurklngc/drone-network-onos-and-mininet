import math

model = 'logDistance'  # default propagation model
exp = 2  # Exponent
sL = 1  # System Loss
lF = 0  # Floor penetration loss factor
pL = 0  # Power Loss Coefficient
nFloors = 0  # Number of floors
gRandom = 0  # Gaussian random variable
variance = 2  # variance
noise_th = -70
cca_threshold = -90
ref_d = 1
a = 12
b = 0.135
uav_default_height = 100
n_los = 1
n_nlos = 20


def path_loss(freq, dist):
    """Path Loss Model:
    (f) signal frequency transmited(Hz)
    (d) is the distance between the transmitter and the receiver (m)
    (c) speed of light in vacuum (m)
    (L) System loss"""
    f = freq * 10 ** 9  # Convert Ghz to Hz
    c = 299792458.0
    L = sL

    if dist == 0: dist = 0.1

    lambda_ = c / f  # lambda: wavelength (m)
    denominator = lambda_ ** 2
    numerator = (4 * math.pi * dist) ** 2 * L
    pl = 10 * math.log10(numerator / denominator)

    return int(pl)


def sum_gains(received_antenna_gain=5, ap_tx_power=14, ap_antenna_gain=5):
    gr = received_antenna_gain
    pt = ap_tx_power
    gt = ap_antenna_gain
    return pt + gt + gr


def get_log_model_rssi(distance, intf_freq, received_antenna_gain=5, ap_tx_power=14, ap_antenna_gain=5):
    """Log Distance Propagation Loss Model:
    ref_d (m): The distance at which the reference loss is
    calculated
    exponent: The exponent of the Path Loss propagation model, where 2
    is for propagation in free space
    (dist) is the distance between the transmitter and the receiver (m)"""
    gains = sum_gains(received_antenna_gain, ap_tx_power, ap_antenna_gain)

    pl = path_loss(intf_freq, ref_d)
    if distance == 0: distance = 0.1

    pldb = 10 * exp * math.log10(distance / ref_d)
    rssi = gains - (int(pl) + int(pldb))

    return float(rssi)


def get_los_nlos_mixture_rssi(distance, intf_freq, received_antenna_gain=5, ap_tx_power=14, ap_antenna_gain=5):
    """LOS/NLOS Mixture Propagation Loss Model:
    ref_d (m): The distance at which the reference loss is
    calculated
    exponent: The exponent of the Path Loss propagation model, where 2
    is for propagation in free space
    (dist) is the distance between the transmitter and the receiver (m)"""
    gains = sum_gains(received_antenna_gain, ap_tx_power, ap_antenna_gain)
    ref_d = 1

    pl = path_loss(intf_freq, ref_d)
    if distance == 0: distance = 0.1

    pldb = 10 * exp * math.log10(distance / ref_d)
    pl_los = pl + pldb + n_los
    pl_nlos = pl + pldb + n_nlos
    elevation_angle = math.asin(uav_default_height / distance) / math.pi * 180
    pr_los = 1 / (1 + 12 * math.exp(-b * (elevation_angle - a)))
    pl_avg = pl_los * pr_los + pl_nlos * (1 - pr_los)
    rssi = gains - pl_avg
    return float(rssi)


def get_log_model_range(intf_freq, received_antenna_gain=5, ap_tx_power=14, ap_antenna_gain=5):
    gains = sum_gains(received_antenna_gain, ap_tx_power, ap_antenna_gain)
    return math.pow(10, ((-noise_th - path_loss(intf_freq, ref_d) + gains) / (10 * exp))) * ref_d


def get_los_nlos_mixture_model_range(intf_freq, received_antenna_gain=5, ap_tx_power=14, ap_antenna_gain=5):
    for i in range(uav_default_height, 9999):
        rssi = get_los_nlos_mixture_rssi(i, intf_freq, received_antenna_gain, ap_tx_power, ap_antenna_gain)
        print("RSSI=%.2f for distance %d" % (rssi, i))
        if rssi < noise_th + 0.1:
            return i
    return -1


if __name__ == '__main__':
    calculated_rssi = get_log_model_rssi(210.44, 2.412)
    print(calculated_rssi)
    calculated_rssi = get_log_model_rssi(75, 2.412)
    print(calculated_rssi)
    # calculated_rssi = get_los_nlos_mixture_rssi(210.44, 2.412)
    print(calculated_rssi)
    calculated_rssi = get_los_nlos_mixture_rssi(200, 2.412)
    print(calculated_rssi)
    calculated_range = get_log_model_range(2.412, ap_tx_power=14)
    print("log_model_range: %f" % calculated_range)
    calculated_range = get_los_nlos_mixture_model_range(2.412, ap_tx_power=23)
    print("los_nlos_mixture_model_range: %f" % calculated_range)
