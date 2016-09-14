#!/bin/bash
set -ex

medlineDir=/projects/jlever/ncbiData/2016/medline
termsFile=BB3_terms.txt
relFile=BB3_relations.txt

outDir=BB3
jobList=jobs.BB3.txt

mkdir -p $outDir

find $medlineDir -name '*.xml' | sort | xargs -I FILE basename FILE | xargs -I FILE echo "jython relatedTermMajigger.py --termsWithSynonymsFile $termsFile --relationsFile $relFile  --removeShortwords --stopwordsFile selected_stopwords.txt --abstractsFile $medlineDir/FILE --outTxtFile $outDir/FILE.txt --outA1File $outDir/FILE.a1" > $jobList
