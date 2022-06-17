REQUEST_INTERVAL=8
NUMBER_OF_SEEDS=10

SEED_OFFSET=0
CATEGORY="vehicle_speed_v6/5"
RECORD_DIR="records/${CATEGORY}"

for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
  python solver.py --record-file $RECORD_FILE &
done

#NUMBER_OF_SEEDS=5
SEED_OFFSET=10
CATEGORY="vehicle_speed_v6/20"
RECORD_DIR="records/${CATEGORY}"

for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
  python solver.py --record-file $RECORD_FILE &
done

NUMBER_OF_SEEDS=10
SEED_OFFSET=50
CATEGORY="vehicle_speed_v6/40"
RECORD_DIR="records/${CATEGORY}"

for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
  python solver.py --record-file $RECORD_FILE &
done
