set -x
REQUEST_INTERVAL=5


NUMBER_OF_SEEDS=10
SEED_OFFSET=110
CATEGORY="vehicle_speed_v2/40"
RECORD_DIR="records/${CATEGORY}"

#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
#  python main.py -m ONLY_CLOUD --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
#  python clean.py
#done
#
#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
#  python main.py -m AGGRESSIVE --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
#  python clean.py
#done

for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
  echo "Record file: $RECORD_FILE"
  python main.py -m AGGRESSIVE --wait-previous-queue --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
  python clean.py
done
