#!/bin/bash
set -ex

# Locations of Python, Jython and where the VERSE scripts are
python=python
jython=jython
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
verseDir=$HERE/..

# Parameters to use for the relation extractor
parameters="C:0.357543477063 ; doFeatureSelection:False ; featureChoice:bigramsOfDependencyPath,dependencyPathElements,dependencyPathNearSelected,ngrams,ngramsOfDependencyPath,ngramsPOS,selectedTokenTypes,selectedlemmas,selectedngramsPOS ; featureSelectPerc:34 ; kernel:linear ; sentenceRange:0 ; svmAutoClassWeights:True ; svmClassWeight:8 ; tfidf:True"
descFile=$HERE/bb.description

# The working directory
outDir=$PWD/tmp.BB3
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
$jython $verseDir/core/TextProcessor.py --inDir BioNLP-ST-2016_BB-event_train_AND_dev --format ST --outFile BioNLP-ST-2016_BB-event_train_AND_dev.verse
$jython $verseDir/core/TextProcessor.py --inDir BioNLP-ST-2016_BB-event_test --format ST --outFile BioNLP-ST-2016_BB-event_test.verse

# Run the relation extractor!
$python $verseDir/core/RelationExtractor.py --trainingFile BioNLP-ST-2016_BB-event_train_AND_dev.verse --testingFile  BioNLP-ST-2016_BB-event_test.verse --relationDescriptions $descFile --outFile out.verse --parameters "$parameters"

# Filter out any incorrect relations
$python $verseDir/utils/Filter.py --inFile out.verse --outFile filtered.verse --relationFilters $descFile

# Export to the results to the ST format
mkdir -p ST
$python $verseDir/utils/ExportToTriggerlessST.py --inFile filtered.verse --outDir ST

# Extract the Gold (the original submitted results)
mkdir $outDir/gold
cd $outDir/gold
unzip $HERE/finalSubmission.BB3.zip
cd $outDir

# Transform the submitted data to the correct format (with E for events instead of R)
perl -pi -e 's/^R/E/g' gold/*.a2

# Copy the TXT and A1 files from the original into the Gold and test directories
cp BioNLP-ST-2016_BB-event_test/*.txt gold
cp BioNLP-ST-2016_BB-event_test/*.a1 gold
cp BioNLP-ST-2016_BB-event_test/*.txt ST
cp BioNLP-ST-2016_BB-event_test/*.a1 ST

# Compare the output of the relation extractor with the original submitted results (and get the overall F1-score)
python $verseDir/evaluation/CompareSTs.py --goldDir gold --testDir ST > evaluate.results
f1score=`cat evaluate.results | grep Summary | grep -oP "F1=[\d\.]*" | cut -f 2 -d '='`

# And finally check that the F1-score is perfect
if [[ "$f1score" == "1.000" ]]; then
	echo "SUCCESS"
else
	echo "ERROR: Results don't match expected"
	exit 255
fi
