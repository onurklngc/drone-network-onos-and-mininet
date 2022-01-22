import collections

import settings
from TaskOrganizer import AssignmentMethod
from sumo_traci import select_vehicle_class

if __name__ == '__main__':
    selections = []
    for i in range(1000):
        selected_class = select_vehicle_class()['type_abbreviation']
        selections.append(selected_class)
    occurrences = collections.Counter(selections)
    print(occurrences)
