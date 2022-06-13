#!/bin/bash
python "$SUMO_HOME/tools/randomTrips.py" -n osm.net.xml  --allow-fringe --fringe-factor 100 -p 8 -o osm.passenger.trips.xml -e 1200 --vehicle-class passenger --vclass passenger  --prefix veh --max-distance 450 --trip-attributes "departLane=\"best\" maxSpeed=\"1.85\"" --fringe-start-attributes "departSpeed=\"max\"" --allow-fringe.min-length 100 --lanes --validate
sumo -c osm.sumocfg --fcd-output sumo_results.xml --seed 1
