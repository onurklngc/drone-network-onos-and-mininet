import logging
import random

import settings as s


def pick_random_location_for_bs(x_min=s.COORDINATE_LIMIT_X[0], x_max=s.COORDINATE_LIMIT_X[1],
                                y_min=s.COORDINATE_LIMIT_Y[0], y_max=s.COORDINATE_LIMIT_Y[1]):
    x = random.choice([x_min + 50, x_max - 50])
    y = random.randint(y_min + 50, y_max - 50)
    return x, y


def pick_coordinate_close_to_given_location(x, y):
    x = random.randint(x - 50, x + 50)
    y = random.randint(y - 50, y + 50)
    return x, y


def get_wait_time(start_time, end_time, period):
    time_passed = end_time - start_time
    logging.debug("Time spent on this step %f" % time_passed)
    time_to_wait = period - time_passed
    if time_to_wait < 0:
        logging.error("Missed deadline by %f" % -time_to_wait)
        time_to_wait = 0
    return time_to_wait
