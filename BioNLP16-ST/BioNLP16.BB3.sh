#!/bin/bash
set -ex

# Locations of Python, Jython and where the VERSE scripts are
python=/gsc/software/linux-x86_64/python-2.7.5/bin/python
jython=jython
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
verseDir=$HERE/..

# Parameters to use for the relation extractor
parameters="C:0.357543477063 ; doFeatureSelection:False ; featureChoice:bigramsOfDependencyPath,dependencyPathElements,dependencyPathNearSelected,ngrams,ngramsOfDependencyPath,ngramsPOS,selectedTokenTypes,selectedlemmas,selectedngramsPOS ; featureSelectPerc:34 ; kernel:linear ; sentenceRange:0 ; svmAutoClassWeights:True ; svmClassWeight:8 ; tfidf:True"
descFile=$HERE/bb.description_new

# The working directory
outDir=tmp.BB3
rm -fr $outDir
mkdir -p $outDir
cd $outDir

# Download all the competition files
wget http://2016.bionlp-st.org/tasks/bb2/BioNLP-ST-2016_BB-event_train.zip
wget http://2016.bionlp-st.org/tasks/bb2/BioNLP-ST-2016_BB-event_dev.zip
wget http://2016.bionlp-st.org/tasks/bb2/BioNLP-ST-2016_BB-event_test.zip

# Unzip the competition files
unzip BioNLP-ST-2016_BB-event_train.zip
unzip BioNLP-ST-2016_BB-event_dev.zip
unzip BioNLP-ST-2016_BB-event_test.zip

# Combine the training and development sets
mkdir BioNLP-ST-2016_BB-event_train_AND_dev
mv BioNLP-ST-2016_BB-event_train/* BioNLP-ST-2016_BB-event_train_AND_dev
mv BioNLP-ST-2016_BB-event_dev/* BioNLP-ST-2016_BB-event_train_AND_dev
rm -fr BioNLP-ST-2016_BB-event_train BioNLP-ST-2016_BB-event_dev

# Remove the Title/Paragraph annotations
perl -i -ne 'print if !/^T\d+\t(Title|Paragraph)/x' BioNLP-ST-2016_BB-event_train_AND_dev/*.a1
perl -i -ne 'print if !/^T\d+\t(Title|Paragraph)/x' BioNLP-ST-2016_BB-event_test/*.a1

# Transform the A2 files so that relations start with E and not R
perl -pi -e 's/^R/E/g' BioNLP-ST-2016_BB-event_train_AND_dev/*.a2

# Run the text processor on the train&dev and test sets
$jython $verseDir/core/TextProcessor.py --inDir BioNLP-ST-2016_BB-event_train_AND_dev --format ST --outFile BioNLP-ST-2016_BB-event_train_AND_dev.pickle
$jython $verseDir/core/TextProcessor.py --inDir BioNLP-ST-2016_BB-event_test --format ST --outFile BioNLP-ST-2016_BB-event_test.pickle

# Run the relation extractor!
$python $verseDir/core/RelationExtractor.py --trainingPickle BioNLP-ST-2016_BB-event_train_AND_dev.pickle --testingPickle  BioNLP-ST-2016_BB-event_test.pickle --rel_descriptions $descFile --outPickle out.pickle --parameters "$parameters"

# Export to the results to the ST format
mkdir -p ST
$python $verseDir/utils/PickleToTriggerlessST.py --inPickle out.pickle --outDir ST

# Filter out any incorrect relations (based on their types)
find ST -name '*.a2' | xargs -I FILE basename FILE | sort | sed -e 's/\.a2//g' | xargs -I FILE echo "$python $verseDir/utils/DataCheck.py $HERE/bb.description BioNLP-ST-2016_BB-event_test/FILE.a1 ST/FILE.a2 ST/FILE.a2" | sh

# Transform the ST data back so that relations start with R (rather than E)
perl -pi -e 's/^E/R/g' ST/*.a2

# Calculate the MD5sum of the results
md5=`find ST -name '*.a2' | sort | xargs cat | md5sum | cut -f 1 -d ' '`
expected=3ca02cf04f67597647aaef69707e1648

# And finally check it
if [[ "$md5" == "$expected" ]]; then
	echo "SUCCESS"
else
	echo "ERROR: Results don't match expected"
	exit 255
fi
