#!/bin/bash

# Call this script from crawl_arxiv_bibtex in terminal

categories=( cs.AI cs.CL cs.CC cs.CE cs.CG cs.GT cs.CV cs.CY cs.CR cs.DS cs.DB cs.DL cs.DM cs.DC cs.ET cs.FL cs.GL cs.GR cs.AR cs.HC cs.IR cs.IT cs.LO cs.LG cs.MS cs.MA cs.MM cs.NI cs.NE cs.NA cs.OS cs.OH cs.PF cs.PL cs.RO cs.SI cs.SE cs.SD cs.SC cs.SY stat.ML )

for category in "${categories[@]}"
do
  echo $category
  python arxivcrawler.py "$category" -m 2500
  echo ""
done
