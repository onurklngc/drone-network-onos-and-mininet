NUMBER_OF_SEEDS=5

#SEED_OFFSET=10
#REQUEST_INTERVAL=5
#CATEGORY="request_interval/${REQUEST_INTERVAL}"
#RECORD_DIR="records/${CATEGORY}"
#
#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
##  echo "Record file: $RECORD_FILE"
#  python solver.py --record-file $RECORD_FILE &
#done
#SEED_OFFSET=400
#REQUEST_INTERVAL=5
#CATEGORY="request_interval/${REQUEST_INTERVAL}"
#RECORD_DIR="records/${CATEGORY}"
#
#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
##  echo "Record file: $RECORD_FILE"
#  python solver.py --record-file $RECORD_FILE &
#done

REQUEST_INTERVAL=10
CATEGORY="request_interval/${REQUEST_INTERVAL}"
RECORD_DIR="records/${CATEGORY}"
#SEED_OFFSET=5
#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
#  python solver.py --record-file $RECORD_FILE &
#done
SEED_OFFSET=300
for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
  python solver.py --record-file $RECORD_FILE &
done

SEED_OFFSET=0
REQUEST_INTERVAL=15
CATEGORY="request_interval/${REQUEST_INTERVAL}"
RECORD_DIR="records/${CATEGORY}"

for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
  python solver.py --record-file $RECORD_FILE &
done
SEED_OFFSET=500
for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
  python solver.py --record-file $RECORD_FILE &
done
