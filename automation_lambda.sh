SEED_OFFSET=20
NUMBER_OF_SEEDS=5
REQUEST_INTERVAL=10
CATEGORY="vehicle_speed/20"
RECORD_DIR="records/${CATEGORY}"

set -x

for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
  echo "Record file: $RECORD_FILE"
  python main.py -m AGGRESSIVE --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL
  python clean.py
  python main.py -m AGGRESSIVE --seed-no $((SEED_OFFSET+i)) --wait-previous-queue --record-file $RECORD_FILE
  python clean.py
  python main.py -m ADAPTIVE --seed-no $((SEED_OFFSET+i)) --record-file $RECORD_FILE
  python clean.py
done
