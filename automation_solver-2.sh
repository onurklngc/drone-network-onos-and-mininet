REQUEST_INTERVAL=5
NUMBER_OF_SEEDS=8

SEED_OFFSET=120
CATEGORY="vehicle_speed_v2/5"
RECORD_DIR="records/${CATEGORY}"

for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
  echo "Record file: $RECORD_FILE"
  python solver.py --record-file $RECORD_FILE
done

#NUMBER_OF_SEEDS=10
#SEED_OFFSET=110
#CATEGORY="vehicle_speed_v2/40"
#RECORD_DIR="records/${CATEGORY}"
#
#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
#  python solver.py --record-file $RECORD_FILE
#done
