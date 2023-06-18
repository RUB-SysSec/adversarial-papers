#!/bin/bash

# Run me with:
# $ bash src/problemspace/tests/compare_pdffiles/run_comparison.sh


COMMIT="6cbf626"

PATHS=(
    "evaluation/submissions/oakland_22/arxiv-sources/submissions_latexpanded/2010.12450"
    "evaluation/submissions/usenix_20/arxiv-sources/submissions_latexpanded/1909.01838"
    "evaluation/submissions/oakland_22/arxiv-sources/submissions_latexpanded/2112.03570"
    "evaluation/submissions/oakland_22/arxiv-sources/submissions_latexpanded/2108.06504"
    "evaluation/submissions/oakland_22/arxiv-sources/submissions_latexpanded/2112.03449"
)

for p in ${PATHS[@]}; do
    python3 src/problemspace/tests/compare_pdffiles/compare.py ${COMMIT} ${p} ${COMMIT}~1 ${p}
done