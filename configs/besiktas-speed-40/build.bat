#!/bin/bash
python "$SUMO_HOME/tools/randomTrips.py" -n osm.net.xml --fringe-factor 1000 -p 7  --intermediate 2 -o osm.passenger.trips.xml -e 1200 --vehicle-class passenger --vclass passenger  --prefix veh --min-distance 300 --trip-attributes "departLane=\"best\" maxSpeed=\"40\"" --fringe-start-attributes "departSpeed=\"max\"" --allow-fringe.min-length 1000 --lanes --validate
sumo -c osm.sumocfg --fcd-output sumo_results.xml --seed 1
