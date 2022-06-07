set -x
REQUEST_INTERVAL=5


NUMBER_OF_SEEDS=10
SEED_OFFSET=120
CATEGORY="vehicle_speed_v2/5"
RECORD_DIR="records/${CATEGORY}"


SEED_ID=123
RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed${SEED_ID}
echo "Record file: $RECORD_FILE"
python main.py -m ONLY_CLOUD --seed-no ${SEED_ID} --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
python clean.py
SEED_ID=125
RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed${SEED_ID}
echo "Record file: $RECORD_FILE"
python main.py -m ONLY_CLOUD --seed-no ${SEED_ID} --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
python clean.py

#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
#  python main.py -m ADAPTIVE --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL
#  python clean.py
#done

#NUMBER_OF_SEEDS=5
#SEED_OFFSET=125
#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
#  python main.py -m ONLY_CLOUD --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
#  python clean.py
#done
#
#NUMBER_OF_SEEDS=10
#SEED_OFFSET=120
#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
#  python main.py -m AGGRESSIVE --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
#  python clean.py
#done
#
#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
#  python main.py -m AGGRESSIVE --wait-previous-queue --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
#  python clean.py
#done
#

