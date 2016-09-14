#!/bin/bash
set -ex

medlineDir=/projects/jlever/ncbiData/2016/medline
termsFile=SeeDev_terms.txt
relFile=SeeDev_relations.txt

outDir=SeeDev
jobList=jobs.SeeDev.txt

mkdir -p $outDir

find $medlineDir -name '*.xml' | sort | xargs -I FILE basename FILE | xargs -I FILE echo "jython relatedTermMajigger.py --termsWithSynonymsFile $termsFile --relationsFile $relFile  --removeShortwords --stopwordsFile selected_stopwords.txt --abstractsFile $medlineDir/FILE --outTxtFile $outDir/FILE.txt --outA1File $outDir/FILE.a1" > $jobList
