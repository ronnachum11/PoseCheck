# ------------------------- POSE MODELS -------------------------


# Downloading the pose-model trained on COCO
COCO_POSE_URL="https://www.dropbox.com/s/2h2bv29a130sgrk/pose_iter_440000.caffemodel"
COCO_FOLDER="models/pose/"
wget -c ${COCO_POSE_URL} -P ${COCO_FOLDER}
