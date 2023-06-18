#!/bin/bash
# Usage: call "bash identify_ifelse.sh <PATH-TO-TPMS-DIR>"

ROOT_DIR_TPMS=$1

PATHS=(
   "${ROOT_DIR_TPMS}/adversarial-papers/evaluation/submissions/usenix_20/arxiv-sources/submissions_latexpanded/"
   "${ROOT_DIR_TPMS}/adversarial-papers/evaluation/submissions/oakland_22/arxiv-sources/submissions_latexpanded/"
)

for submissions_dir in ${PATHS[@]}; do
  echo ""; echo ""; echo "*******"
  echo "Test ${submissions_dir}"
  echo "*******"

  echo ""; echo "Test iffalse...."
  find ${submissions_dir} -type f -name "*main.tex" -exec grep -niH "\\iffalse" {} \;

  echo ""; echo "Test ifodd...."
  find ${submissions_dir} -type f -name "*main.tex" -exec grep -niH "\\ifodd" {} \;

  echo ""; echo "Test if0...."
  find ${submissions_dir} -type f -name "*main.tex" -exec grep -niH "\\\if0" {} \;

  echo ""; echo "Test ifnum...."
  find ${submissions_dir} -type f -name "*main.tex" -exec grep -niH "\\\ifnum" {} \;

  echo ""; echo "Test ifthenelse...."
  find ${submissions_dir} -type f -name "*main.tex" -exec grep -niH "\\\ifthenelse" {} \;
done
