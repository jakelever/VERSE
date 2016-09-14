#!/bin/bash
set -ex

f=/projects/jlever/ncbiData/2016/filteredMedline/1950.medline16n0016.xml
jython relatedTermMajigger.py --termsWithSynonymsFile BB3_terms.txt --relationsFile BB3_relations.txt --removeShortwords --stopwordsFile selected_stopwords.txt --abstractsFile $f --outTxtFile out.txt --outA1File out.a1
