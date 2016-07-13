#!/bin/bash
set -ex

trainFile=$1
trainDir=$2
devFile=$3
devDir=$4
descFile=$5
resultsDir=$6

centOSVersion=`rpm -qa \*-release | grep -Ei "oracle|redhat|centos" | cut -d"-" -f3`
if [[ $centOSVersion == "5" ]]; then
	python=/gsc/software/linux-x86_64-centos5/Anaconda-2.3.0/anaconda/bin/python
else	
	python=/gsc/software/linux-x86_64/python-2.7.5/bin/python
fi

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
verseDir=$SCRIPTDIR/..

timestamp=`date +%s`
uniqueName=$HOSTNAME.$$.$timestamp
outDir=tmpOut/$uniqueName
outFile=tmpOut/$uniqueName.verse

randNum=$(($RANDOM%200))
logDir=$resultsDir/$randNum
mkdir -p $logDir

oldParameters=
resultCount=`find $resultsDir -name '*.results'  | wc -l`
if [ $resultCount -ge 100 ]; then
	oldParameterFile=`find $resultsDir -name '*.results' | xargs -I FILE grep -H 0 FILE | sort -k4,4n -t '=' | tail -n 100 | cut -f 1 -d ':' | awk ' { print rand()"\t"$0; } ' | sort -k1,1nr -t $'\t' | head -n 1 | cut -f 2 -d $'\t' | sed -e 's/\.results$/\.parameters/'`
	oldParameters=`cat $oldParameterFile`
fi

parameters=`$python $verseDir/utils/GenerateParameters.py --parameters "$oldParameters"`

echo "$parameters" > $logDir/$uniqueName.parameters

mkdir -p $outDir
$python $verseDir/core/RelationExtractor.py --trainingFile $trainFile --testingFile $devFile --outFile $outFile --parameters "$parameters" --relationDescriptions $descFile > $logDir/$uniqueName.1.log
$python $verseDir/utils/ExportToTriggerlessST.py --inFile $outFile --outDir $outDir
$python $verseDir/evaluation/CompareSTs.py --goldDir $devDir --testDir $outDir > $logDir/$uniqueName.results1
rm -fr $outDir
rm -f $outFile

mkdir -p $outDir
$python $verseDir/core/RelationExtractor.py --trainingFile $devFile --testingFile $trainFile --outFile $outFile --parameters "$parameters" --relationDescriptions $descFile > $logDir/$uniqueName.2.log
$python $verseDir/utils/ExportToTriggerlessST.py --inFile $outFile --outDir $outDir
$python $verseDir/evaluation/CompareSTs.py --goldDir $trainDir --testDir $outDir > $logDir/$uniqueName.results2
rm -fr $outDir
rm -f $outFile

averageF1Score=`cat $logDir/$uniqueName.results1 $logDir/$uniqueName.results2 | grep Summary | cut -f 4 -d '=' | awk ' { total = total + $1; count = count + 1; } END { print total/count; }  '`

echo "$averageF1Score" > $logDir/$uniqueName.results

echo "Average F1-score for run: $averageF1Score"

