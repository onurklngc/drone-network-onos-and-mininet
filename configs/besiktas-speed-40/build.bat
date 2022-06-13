#!/bin/bash
python "$SUMO_HOME/tools/randomTrips.py" -n osm.net.xml --fringe-factor 1000 -p 11  --intermediate 5 -o osm.passenger.trips.xml -e 1200 --vehicle-class passenger --vclass passenger  --prefix veh --min-distance 700 --trip-attributes "departLane=\"best\" maxSpeed=\"14\"" --fringe-start-attributes "departSpeed=\"max\"" --allow-fringe.min-length 100 --lanes --validate
sumo -c osm.sumocfg --fcd-output sumo_results.xml --seed 1
