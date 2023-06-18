#!/bin/bash -xe

source ~/.virtualenvs/tpms/bin/activate

PRG="python3 ./synonyms.py train"
DATA="sp_small.json committees_full.json sp_blackbox.json sp_full.json"
DATADIR=".."

for CORPUS in $DATA ; do
  MODEL="models/`basename $CORPUS .json`"
  $PRG -c config-nostem.yml -r $DATADIR/$CORPUS -m $MODEL-nostem.w2v.gz
  $PRG -c config-stem.yml -r $DATADIR/$CORPUS -m $MODEL-stem.w2v.gz
done
