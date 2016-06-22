#!/bin/bash
set -ex

# Locations of Python, Jython and where the VERSE scripts are
python=/gsc/software/linux-x86_64/python-2.7.5/bin/python
jython=jython
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
verseDir=$HERE/..

# Parameters to use for the relation extractor
parameters="doFeatureSelection:True ; featureChoice:dependencyPathElements,dependencyPathNearSelected,ngrams,ngramsPOS,selectedTokenTypes,splitAcrossSentences ; featureSelectPerc:5 ; kernel:linear ; sentenceRange:0 ; svmAutoClassWeights:False ; svmClassWeight:5 ; tfidf:True"
descFile=$HERE/seedev.description2

# The working directory
outDir=tmp.SeeDev
rm -fr $outDir
mkdir -p $outDir
cd $outDir

# Download all the competition files
wget http://2016.bionlp-st.org/tasks/seedev/BioNLP-ST-2016_SeeDev-binary_train.zip
wget http://2016.bionlp-st.org/tasks/seedev/BioNLP-ST-2016_SeeDev-binary_dev.zip
wget http://2016.bionlp-st.org/tasks/seedev/BioNLP-ST-2016_SeeDev-binary_test.zip

# Unzip the competition files
unzip BioNLP-ST-2016_SeeDev-binary_train.zip
unzip BioNLP-ST-2016_SeeDev-binary_dev.zip
unzip BioNLP-ST-2016_SeeDev-binary_test.zip

# Combine the training and development sets
mkdir BioNLP-ST-2016_SeeDev-binary_train_AND_dev
mv BioNLP-ST-2016_SeeDev-binary_train/* BioNLP-ST-2016_SeeDev-binary_train_AND_dev
mv BioNLP-ST-2016_SeeDev-binary_dev/* BioNLP-ST-2016_SeeDev-binary_train_AND_dev
rm -fr BioNLP-ST-2016_SeeDev-binary_train BioNLP-ST-2016_SeeDev-binary_dev

# Run the text processor on the train&dev and test sets
$jython $verseDir/core/TextProcessor.py --inDir BioNLP-ST-2016_SeeDev-binary_train_AND_dev --format ST --outFile BioNLP-ST-2016_SeeDev-binary_train_AND_dev.pickle
$jython $verseDir/core/TextProcessor.py --inDir BioNLP-ST-2016_SeeDev-binary_test --format ST --outFile BioNLP-ST-2016_SeeDev-binary_test.pickle

# Run the relation extractor!
$python $verseDir/core/RelationExtractor.py --trainingPickle BioNLP-ST-2016_SeeDev-binary_train_AND_dev.pickle --testingPickle BioNLP-ST-2016_SeeDev-binary_test.pickle --rel_descriptions $descFile --outPickle out.pickle --parameters "$parameters"

# Export to the results to the ST format
mkdir -p ST
$python $verseDir/utils/PickleToTriggerlessST.py --inPickle out.pickle --outDir ST

# Filter out any incorrect relations (based on their types)
find ST -name '*.a2' | xargs -I FILE basename FILE | sort | sed -e 's/\.a2//g' | xargs -I FILE echo "$python $verseDir/utils/DataCheck.py $HERE/seedev.description BioNLP-ST-2016_SeeDev-binary_test/FILE.a1 ST/FILE.a2 ST/FILE.a2" | sh

# Calculate the MD5sum of the results
md5=`find ST -name '*.a2' | sort | xargs cat | md5sum | cut -f 1 -d ' '`
expected=302957741abd68de2bac5a5c514bc230

# And finally check it
if [[ "$md5" == "$expected" ]]; then
	echo "SUCCESS"
else
	echo "ERROR: Results don't match expected"
	exit 255
fi

