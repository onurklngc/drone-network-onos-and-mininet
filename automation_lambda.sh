SEED_OFFSET=10
NUMBER_OF_SEEDS=5
REQUEST_INTERVAL=5
CATEGORY="request_interval/5"
RECORD_DIR="records/${CATEGORY}"

set -x

for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
  echo "Record file: $RECORD_FILE"
  python main.py -m ONLY_CLOUD --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
  python clean.py
done

SEED_OFFSET=400
NUMBER_OF_SEEDS=5
REQUEST_INTERVAL=5
CATEGORY="request_interval/5"
RECORD_DIR="records/${CATEGORY}"

set -x

for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
  echo "Record file: $RECORD_FILE"
  python main.py -m ONLY_CLOUD --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
  python clean.py
done

SEED_OFFSET=5
NUMBER_OF_SEEDS=5
REQUEST_INTERVAL=10
CATEGORY="request_interval/10"
RECORD_DIR="records/${CATEGORY}"
for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
  echo "Record file: $RECORD_FILE"
  python main.py -m ONLY_CLOUD --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
  python clean.py
done

SEED_OFFSET=300
NUMBER_OF_SEEDS=5
REQUEST_INTERVAL=10
CATEGORY="request_interval/10"
RECORD_DIR="records/${CATEGORY}"
for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
  echo "Record file: $RECORD_FILE"
  python main.py -m ONLY_CLOUD --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
  python clean.py
done

SEED_OFFSET=0
NUMBER_OF_SEEDS=5
REQUEST_INTERVAL=15
CATEGORY="request_interval/15"
RECORD_DIR="records/${CATEGORY}"
for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
  echo "Record file: $RECORD_FILE"
  python main.py -m ONLY_CLOUD --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
  python clean.py
done

SEED_OFFSET=500
NUMBER_OF_SEEDS=5
REQUEST_INTERVAL=15
CATEGORY="request_interval/15"
RECORD_DIR="records/${CATEGORY}"
for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
  echo "Record file: $RECORD_FILE"
  python main.py -m ONLY_CLOUD --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
  python clean.py
done
