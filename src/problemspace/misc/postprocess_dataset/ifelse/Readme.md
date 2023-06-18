# Instructions

1. Call bash identify_ifelse.sh <path-to-TPMS-root>
2. Check all findings and remove if necessary
3. Use src/problemspace/tests/compare_pdffiles/ scripts to check if your manual changes have not changed the PDF
   1. To this end, aftter changing tex files, commit locally!
   2. Adjust the commit hash & add all paths that you have changed
   3. Call ```bash run_comparison.sh``` 
   4. You should get no warnings!
