#!/bin/bash
set -ex

centOSVersion=`rpm -qa \*-release | grep -Ei "oracle|redhat|centos" | cut -d"-" -f3`
if [[ $centOSVersion == "5" ]]; then
	python=/gsc/software/linux-x86_64-centos5/Anaconda-2.3.0/anaconda/bin/python
else	
	python=/gsc/software/linux-x86_64/python-2.7.5/bin/python
fi

timestamp=`date +%s`
uniqueName=$HOSTNAME.$$.$timestamp

resultsDir=crossvalidation/seedev
outDir=tmpOut/$uniqueName

randNum=$(($RANDOM%200))
logDir=$resultsDir/$randNum
mkdir -p $logDir

oldParameters=
resultCount=`find $resultsDir -name '*.results'  | wc -l`
if [ $resultCount -ge 10 ]; then
	#oldParameterFile=`find $resultsDir -name '*.results' | awk ' { print rand()"\t"$0; } ' | sort -k1,1nr -t $'\t' | head -n 1000 | cut -f 2 -d $'\t' | xargs -I FILE grep -H Summary FILE | sort -k4,4n -t '=' | tail -n 1 | cut -f 1 -d ':' | sed -e 's/\.results$/\.parameters/'`
	oldParameterFile=`find $resultsDir -name '*.results' | xargs -I FILE grep -H 0 FILE | sort -k4,4n -t '=' | tail -n 100 | cut -f 1 -d ':' | awk ' { print rand()"\t"$0; } ' | sort -k1,1nr -t $'\t' | head -n 1 | cut -f 2 -d $'\t' | sed -e 's/\.results$/\.parameters/'`
	oldParameters=`cat $oldParameterFile`
fi

#parameters="$doTrim:1 ; featureSelectPerc:$perc ; classWeight:$weight ; svmKernel:$kernel"

parameters=`$python GenerateParameters.py --parameters "$oldParameters"`

trainPickle=BioNLP-ST-2016_SeeDev-binary_train.pickle
devPickle=BioNLP-ST-2016_SeeDev-binary_dev.pickle

echo "$parameters" > $logDir/$uniqueName.parameters

mkdir -p $outDir
$python RelationExtractor.py --trainingPickle $trainPickle --testingPickle $devPickle --outDir $outDir --parameters "$parameters" --rel_descriptions seedev.description2 > $logDir/$uniqueName.1.log
$python Evaluate.py --goldDir ../Data/BioNLP-ST-2016_SeeDev-binary_dev/ --testDir $outDir > $logDir/$uniqueName.results1
rm -fr $outDir

mkdir -p $outDir
$python RelationExtractor.py --trainingPickle $devPickle --testingPickle $trainPickle --outDir $outDir --parameters "$parameters" --rel_descriptions seedev.description2 > $logDir/$uniqueName.2.log
$python Evaluate.py --goldDir ../Data/BioNLP-ST-2016_SeeDev-binary_train/ --testDir $outDir > $logDir/$uniqueName.results2
rm -fr $outDir

cat $logDir/$uniqueName.results1 $logDir/$uniqueName.results2 | grep Summary | cut -f 4 -d '=' | awk ' { total = total + $1; count = count + 1; } END { print total/count; }  ' > $logDir/$uniqueName.results

