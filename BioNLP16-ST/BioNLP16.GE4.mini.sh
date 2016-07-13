#!/bin/bash
set -ex

# This is a cut-down version that tests the full pipeline using only a subset of the GE4 data (used for faster integration testing)

# Locations of Python, Jython and where the VERSE scripts are
python=/gsc/software/linux-x86_64/python-2.7.5/bin/python
jython=jython
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
verseDir=$HERE/..

# Location of parameter files
auxDir=$HERE/GE4_auxFiles

# The working directory
outDir=tmp.GE4Mini
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

# Trim it down to a smaller set
find bionlp-st-ge-2016-reference/ -name '*.json' | sort | tail -n +20 | xargs rm
find bionlp-st-ge-2016-test-proteins/ -name '*.json' | sort | tail -n +20 | xargs rm

# Fix the various files (remove duplicates and rename non-protein entities to have EE id - to be predicted)
find bionlp-st-ge-2016-* -name '*.json' | xargs -I FILE $python $verseDir/utils/RemoveDuplicatesInJSON.py FILE
find bionlp-st-ge-2016-* -name '*.json' | xargs -I FILE $python $verseDir/utils/CleanupGE4Data.py FILE

# Filenames and directories to work with
trainOrig=train.verse
test=test.verse
trainJsonDir=bionlp-st-ge-2016-reference
testJsonDir=bionlp-st-ge-2016-test-proteins

# Set entities that are "known" through-out
knownEntities="Protein"

# Run the text processor (note that --splitTokensForGE4 option)
$jython $verseDir/core/TextProcessor.py --format JSON --inDir $trainJsonDir --outFile $trainOrig --splitTokensForGE4 --knownEntities "$knownEntities"
$jython $verseDir/core/TextProcessor.py --format JSON --inDir $testJsonDir --outFile $test --splitTokensForGE4 --knownEntities "$knownEntities"

# Load the paramters
parameters="featureChoice:ngrams; doFeatureSelection:True; featureSelectPerc:5; kernel:linear"
entity_parameters=$parameters
rel_parameters=$parameters
modSpeculationparameters=$parameters
modNegationparameters=$parameters

# Add on additional filtering parameter necessary for the GE4 task
rel_parameters="$rel_parameters ; doFiltering:True"

# Clear out any predicted data from the test file
$python $verseDir/utils/RemovePredicted.py --inFile $test --outFile start.verse

# Run the entity predictor
$python $verseDir/core/EntityExtractor.py --trainingFile $trainOrig --testingFile start.verse --outFile entities.verse --parameters "$entity_parameters" --entityDescriptions $auxDir/entity.descriptions

# Run the relation extractor
$python $verseDir/core/RelationExtractor.py --trainingFile $trainOrig --testingFile entities.verse --outFile relations.verse --parameters "$rel_parameters" --relationDescriptions $auxDir/rel.filters

# Run the mod extractor (for speculation)
$python $verseDir/core/ModificationExtractor.py --trainingFile $trainOrig --testingFile relations.verse --outFile modSpeculation.verse --parameters "$modSpeculationparameters" --modificationDescriptions $auxDir/mod.speculation

# Run the mod extractor (for negation)
$python $verseDir/core/ModificationExtractor.py --trainingFile $trainOrig --testingFile modSpeculation.verse --outFile modSpeculationNegation.verse --parameters "$modNegationparameters" --modificationDescriptions $auxDir/mod.negation --mergeWithExisting

# Filter the results for correct relations and modifications
$python $verseDir/utils/Filter.py --relationFilters $auxDir/rel.filters --modificationFilters $auxDir/mod.filters --inFile modSpeculationNegation.verse --outFile filtered.verse

# Link the final version
ln -s filtered.verse final.verse

# Export the results to JSON
triggerTypes="Acetylation,Binding,Deacetylation,Gene_expression,Localization,Negative_regulation,Phosphorylation,Positive_regulation,Protein_catabolism,Protein_modification,Regulation,Transcription,Ubiquitination"
mkdir json
$python $verseDir/utils/ExportToJSON.py --inFile final.verse --outDir json --triggerTypes "$triggerTypes" --origDir bionlp-st-ge-2016-test-proteins

# Calculate the MD5sum of the results
md5=`find json -name '*.json' | sort | xargs cat | md5sum | cut -f 1 -d ' '`
expected=4a9f6e34c999d1621da53fc09afac589

# Compare with expected and output
if [[ "$md5" == "$expected" ]]; then
	echo "SUCCESS"
else
	echo "ERROR: Results don't match expected"
	exit 255
fi
