#!/bin/bash

# Run me with:
# $ bash src/problemspace/tests/compare_pdffiles/run_comparison.sh

COMMIT="228b900"

PATHS=(
    "evaluation/submissions/oakland_22/arxiv-sources/submissions_latexpanded/2104.02739"
    "evaluation/submissions/oakland_22/arxiv-sources/submissions_latexpanded/2108.09293"
    "evaluation/submissions/oakland_22/arxiv-sources/submissions_latexpanded/2108.01341"
)

for p in ${PATHS[@]}; do
    python3 src/problemspace/tests/compare_pdffiles/compare.py ${COMMIT} ${p} ${COMMIT}~1 ${p}
done