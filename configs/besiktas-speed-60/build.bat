#!/bin/bash
python "$SUMO_HOME/tools/randomTrips.py" -n osm.net.xml --fringe-factor 1000 -p 11 --intermediate 7 -o osm.passenger.trips.xml -e 1200 --vehicle-class passenger --vclass passenger  --prefix veh --min-distance 700 --max-distance 3500 --trip-attributes "departLane=\"best\" maxSpeed=\"23\"" --fringe-start-attributes "departSpeed=\"max\"" --allow-fringe.min-length 100 --lanes --validate
sumo -c osm.sumocfg --fcd-output sumo_results.xml --seed 1
