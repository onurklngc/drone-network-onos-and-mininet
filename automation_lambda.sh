set -x
REQUEST_INTERVAL=8


NUMBER_OF_SEEDS=6
SEED_OFFSET=14
CATEGORY="vehicle_speed_v6/20"
RECORD_DIR="records/${CATEGORY}"

simulate_category () {
for i in $(seq 1 "$NUMBER_OF_SEEDS")
do
  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
  echo "Record file: $RECORD_FILE"
  python main.py -m ADAPTIVE --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL
  python clean.py
  chmod 777 -R .
  python main.py -m AGGRESSIVE --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
  python clean.py
  chmod 777 -R .
  python main.py -m ONLY_CLOUD --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
  python clean.py
  chmod 777 -R .
  python main.py -m AGGRESSIVE --wait-previous-queue --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
  python clean.py
  chmod 777 -R .
done
}
simulate_category
#NUMBER_OF_SEEDS=1
#SEED_OFFSET=10
#CATEGORY="vehicle_speed_v4/20"
#RECORD_DIR="records/${CATEGORY}"
#
#simulate_category
#NUMBER_OF_SEEDS=1
#SEED_OFFSET=20
#CATEGORY="vehicle_speed_v4/60"
#RECORD_DIR="records/${CATEGORY}"
#simulate_category

#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
#  python main.py -m ADAPTIVE --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL
#  python clean.py
#done
#
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
#
#for i in $(seq 1 "$NUMBER_OF_SEEDS")
#do
#  RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed$((SEED_OFFSET+i))
#  echo "Record file: $RECORD_FILE"
#  python main.py -m AGGRESSIVE --wait-previous-queue --seed-no $((SEED_OFFSET+i)) --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
#  python clean.py
#done

#SEED_ID=123
#RECORD_FILE=${RECORD_DIR}/lambda${REQUEST_INTERVAL}_seed${SEED_ID}
#echo "Record file: $RECORD_FILE"
#python main.py -m ONLY_CLOUD --seed-no ${SEED_ID} --request-interval $REQUEST_INTERVAL --record-file $RECORD_FILE
#python clean.py
