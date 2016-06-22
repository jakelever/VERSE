#!/bin/bash
set -e -x

SCRIPTBASE=$PWD/..
TESTBASE=$PWD
TOOLSBASE=$PWD/../../tools
#script=$PWD/../RelationExtractor.py

testType="selectedngrams"
featureChoice="selectedngrams"
parameters="featureChoice:$featureChoice"

workingDir=tmp
workingDir=`readlink -f $workingDir`
rm -fr $workingDir
mkdir -p $workingDir
cd $workingDir

python=/gsc/software/linux-x86_64/python-2.7.5/bin/python
jython=jython

mkdir -p testSet
mkdir -p testSet/train
mkdir -p testSet/goldTest
mkdir -p testSet/testNoA2
mkdir -p out

trainCount=1000
testCount=1000

# Generate test data
$python $TESTBASE/GenerateTestData.py --outTxtFile testSet/train/0000.txt --outA1File testSet/train/0000.a1 --outA2File testSet/train/0000.a2 --testType $testType --exampleCount $trainCount --triggerless
$python $TESTBASE/GenerateTestData.py --outTxtFile testSet/goldTest/0000.txt --outA1File testSet/goldTest/0000.a1 --outA2File testSet/goldTest/0000.a2 --testType $testType --exampleCount $testCount --triggerless

cp testSet/goldTest/*.txt testSet/goldTest/*.a1 testSet/testNoA2

# Let's parse the text
jython $SCRIPTBASE/TextProcessor.py --inDir testSet/train --outFile train.pickle
jython $SCRIPTBASE/TextProcessor.py --inDir testSet/testNoA2 --outFile testNoA2.pickle

descriptionFile=descriptions.txt
echo -e "Gene_expression;Cause;Theme\tGene_expression\tProtein" >> $descriptionFile
echo -e "Positive_regulation;Cause;Theme\tPositive_regulation\tProtein" >> $descriptionFile

# And now let's try to extract them
$python $SCRIPTBASE/RelationExtractor.py --trainingPickle train.pickle --testingPickle testNoA2.pickle --outDir out --parameters "$parameters" --rel_descriptions $descriptionFile

cp testSet/testNoA2/* out/

$python $SCRIPTBASE/Evaluate.py --goldDir $workingDir/testSet/goldTest --testDir $workingDir/out

#cd $workingDir/out
#$TOOLSBASE/a2-normalize.pl -u *.a2
#cd $workingDir/testSet/goldTest
#$TOOLSBASE/a2-normalize.pl -u *.a2

#cd $workingDir/out
#$TOOLSBASE/a2-evaluate.pl -g $workingDir/testSet/goldTest *.a2
