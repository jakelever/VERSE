#!/bin/bash
set -ex

# Locations of Python, Jython and where the VERSE scripts are
python=/gsc/software/linux-x86_64/python-2.7.5/bin/python
jython=jython
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
verseDir=$HERE/..

# Location of parameter files
auxDir=$HERE/GE4_auxFiles

# The working directory
outDir=tmp.GE4
rm -fr $outDir
mkdir -p $outDir
cd $outDir

# Download and extract the training set
wget http://pubannotation.org/projects/bionlp-st-ge-2016-reference/annotations.tgz
mv annotations.tgz bionlp-st-ge-2016-reference.tgz
tar xvf bionlp-st-ge-2016-reference.tgz

# Download and extract the test set
wget http://pubannotation.org/projects/bionlp-st-ge-2016-test-proteins/annotations.tgz
mv annotations.tgz bionlp-st-ge-2016-test-proteins.tgz
tar xvf bionlp-st-ge-2016-test-proteins.tgz

# Fix the various files (remove duplicates and rename non-protein entities to have EE id - to be predicted)
find bionlp-st-ge-2016-* -name '*.json' | xargs -I FILE $python $verseDir/utils/RemoveDuplicatesInJSON.py FILE
find bionlp-st-ge-2016-* -name '*.json' | xargs -I FILE $python $verseDir/utils/FixJSONData.py FILE

# Filenames and directories to work with
trainOrig=train.pickle
test=test.pickle
trainJsonDir=bionlp-st-ge-2016-reference
testJsonDir=bionlp-st-ge-2016-test-proteins

# Run the text processor (note that --splitTokensForGE4 option)
$jython $verseDir/core/TextProcessor.py --format JSON --inDir $trainJsonDir --outFile $trainOrig --splitTokensForGE4
$jython $verseDir/core/TextProcessor.py --format JSON --inDir $testJsonDir --outFile $test --splitTokensForGE4

# Load the paramters
entity_parameters="`cat $auxDir/entity.parameters`"
rel_parameters="`cat $auxDir/relation.parameters`"
modSpeculationparameters="`cat $auxDir/mod.speculation.parameters`"
modNegationparameters="`cat $auxDir/mod.negation.parameters`"

# Add on additional parameters necessary for the GE4 task"
rel_parameters="$rel_parameters ; doGE4Things:True ; doFiltering:True"

# Clear out any predicted data from the test file
$python $verseDir/utils/RemovePredicted.py --inPickle $test --outPickle start.pickle

# Run the entity predictor
$python $verseDir/core/EntityExtractor.py --trainingPickle $trainOrig --testingPickle start.pickle --outPickle entities.pickle --parameters "$entity_parameters" --entity_descriptions $auxDir/entity.descriptions

# Run the relation extractor
$python $verseDir/core/RelationExtractor.py --trainingPickle $trainOrig --testingPickle entities.pickle --outPickle relations.pickle --parameters "$rel_parameters" --rel_descriptions $auxDir/rel.filters

# Run the mod extractor (for speculation)
$python $verseDir/core/ModificationExtractor.py --trainingPickle $trainOrig --testingPickle relations.pickle --outPickle modSpeculation.pickle --parameters "$modSpeculationparameters" --modification_descriptions $auxDir/mod.speculation

# Run the mod extractor (for negation)
$python $verseDir/core/ModificationExtractor.py --trainingPickle $trainOrig --testingPickle modSpeculation.pickle --outPickle modSpeculationNegation.pickle --parameters "$modNegationparameters" --modification_descriptions $auxDir/mod.negation --mergeWithExisting

# Filter the results for correct relations and modifications
$python $verseDir/utils/FilterPickle.py --rel_filters $auxDir/rel.filters --mod_filters $auxDir/mod.filters --inPickle modSpeculationNegation.pickle --outPickle filtered.pickle

# Link the final version
ln -s filtered.pickle final.pickle

# Export the results to JSON
triggerTypes="Acetylation,Binding,Deacetylation,Gene_expression,Localization,Negative_regulation,Phosphorylation,Positive_regulation,Protein_catabolism,Protein_modification,Regulation,Transcription,Ubiquitination"
mkdir json
$python $verseDir/utils/PickleToJson.py --inPickle final.pickle --outDir json --triggerTypes "$triggerTypes" --origDir bionlp-st-ge-2016-test-proteins

# Calculate the MD5sum of the results
md5=`find json -name '*.json' | sort | xargs cat | md5sum | cut -f 1 -d ' '`
expected=68e04f8b2c9af21395e0ff3a5a3048f3

# Compare with expected and output
if [[ "$md5" == "$expected" ]]; then
	echo "SUCCESS"
else
	echo "ERROR: Results don't match expected"
	exit 255
fi
