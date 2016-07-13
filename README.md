# VERSE v1.0

This is the repo for the Vancouver Event and Relation System for Extraction (VERSE) project. It is a biomedical event and relation extractor designed for knowledge base construction purposes. It competed in the [BioNLP'16 Shared Task](http://2016.bionlp-st.org/) and placed first in the [Bacteria Biotope event subtask](http://2016.bionlp-st.org/tasks/bb2/bb3-evaluation)  and third in the [Seed Development binary event subtask](http://2016.bionlp-st.org/tasks/seedev/seedev-evaluation).

## How does it work (briefly)?

VERSE uses the Stanford CoreNLP tools to parse a corpus of text in order to get tokens, parts-of-speech and dependency graph information. With a suitable training set, the resulting parsed data is then vectorised and fed into scikit-learn classifiers (either SVM or LogisticRegression). The  predictions can then be exported out to a JSON format or the standard format used in BioNLP Shared Tasks (known as ST format).

## What types of things can it predict?

VERSE can predict entities, relations and modifiers. The full event extraction pipeline uses these three prediction systems in sequence (as used in the [Genia Extraction subtask](http://2016.bionlp-st.org/tasks/ge4) of BioNLP'16 ST). The predictors can be used individually as well.

## What dependencies does VERSE have?

VERSE relies on the following things
- [Python 2.7](https://www.python.org/)
- [Jython](http://www.jython.org/)
- [scikit-learn](http://scikit-learn.org/)
- [Stanford CoreNLP](http://stanfordnlp.github.io/CoreNLP/)
- [intervaltree](https://pypi.python.org/pypi/intervaltree/2.0.4)
- [NetworkX](https://networkx.github.io/)

## What's in this repo?

- [core](core/) - The main tools for text processing and prediction
- [utils](utils/) - Utilities to filter the input and output of VERSE (e.g. for invalid relations) and also to export to various formats.
- [evaluation](evaluation/) - Scripts to evaluate the results of VERSE
- [BioNLP16-ST](BioNLP16-ST/) - Scripts to run VERSE with the correct settings for the entries to the different subtasks in the BioNLP'16 Shared Task.

## Example Usage

The basic usage of VERSE involves first parsing text, then predicting entities, relations and modifications separately, and finally filtering and exporting. Here's the breakdown and explanation for running the GE4 dataset. The code below assumes that $python points towards an appropriate version of Python 2.7, $jython points towards jython and $verseDir points towards the root of VERSE. Note that these examples aren't used the parameters used for the competition. Smaller parameter sets are used for explanation. Check the [BioNLP16-ST/GE4_auxFiles](BioNLP16-ST/GE4_auxFiles) directory for the actual parameter sets used.

This shows the full pipeline but entity/modification extraction could be skipped if only relation extraction is required. Each step uses the output file from the previous stage.

### Getting the data

First we'll download the appropriate files (the training set and the test set)

```shell
wget http://pubannotation.org/projects/bionlp-st-ge-2016-reference/annotations.tgz
mv annotations.tgz bionlp-st-ge-2016-reference.tgz
tar xvf bionlp-st-ge-2016-reference.tgz

wget http://pubannotation.org/projects/bionlp-st-ge-2016-test-proteins/annotations.tgz
mv annotations.tgz bionlp-st-ge-2016-test-proteins.tgz
tar xvf bionlp-st-ge-2016-test-proteins.tgz
```

### Some preprocessing
This is only really needed for the GE4 dataset and involves removing duplicates from the official data and also correcting the types of some entities (specifically, "Protein_domain" & "DNA" to "Entity")

```shell
find bionlp-st-ge-2016-* -name '*.json' | xargs -I FILE $python $verseDir/utils/RemoveDuplicatesInJSON.py FILE
find bionlp-st-ge-2016-* -name '*.json' | xargs -I FILE $python $verseDir/utils/CleanupGE4Data.py FILE
```

### Text Processing

Next we run the text through the Stanford CoreNLP pipeline using the TextProcessor script. In this case we're also using the --splitTokensForGE4 to deal with tokens that contain subparts, likek "ALK-dependent". And the --knownEntities parameter keeps track of which entities won't need to be predicted for this project (i.e. we should always have Proteins annotated).

```shell
$jython $verseDir/core/TextProcessor.py --format JSON --inDir bionlp-st-ge-2016-reference --outFile trainOrig.verse --splitTokensForGE4 --knownEntities "Protein"
$jython $verseDir/core/TextProcessor.py --format JSON --inDir bionlp-st-ge-2016-test-proteins --outFile test.verse --splitTokensForGE4 --knownEntities "Protein"
```

### Clear Predicted

This is unnecessary here, but is important when working with fully annotated data for parameter optimisation. This basically removes any predictions currently in a VERSE file

```shell
$python $verseDir/utils/RemovePredicted.py --inFile test.verse --outFile start.verse
```

### Entity Extraction

This takes in the annotated training VERSE file, vectorises it and trains a classifier. It then vectorises the test VERSE file and predicts entities on it. We'll use some basic parameters here as examples.

```shell
$python $verseDir/core/EntityExtractor.py --trainingFile trainOrig.verse --testingFile start.verse --outFile entities.verse --parameters "classifier:SVM ; doFeatureSelection:False ; featureChoice:ngrams,bigrams_entityWindowRight_4" --entityDescriptions $verseDir/BioNLP16-ST/GE4_auxFiles/entity.descriptions
```

The --parameters option takes a semi-colon delimited list of parameters for the vectorizer and classifier. The example above is telling it to use an SVM, not do feature selection and use ngrams as well as a bigrams window (including 4 tokens to the right of each entity).

The --entityDescriptions option is a file that simply contains the names of all entities that should be predicted.

### Relation Extraction

Now we do basically the same thing for relations: vectorize and train using the training file, and then predict on the test file (notice that we've used the output from the last extractor).

```shell
$python $verseDir/core/RelationExtractor.py --trainingFile trainOrig.verse --testingFile entities.verse --outFile relations.verse --parameters "classifier:LogisticRegression ; doFeatureSelection:True ; featureSelectPerc:30 ; tfidf:True ; doFiltering:True ; sentenceRange:1; featureChoice:ngrams" --relationDescriptions $verseDir/BioNLP16-ST/GE4_auxFiles/rel.filters
```

The --parameters option works exactly the same as the entity extraction. This time it instructs the extractor to use a logistic regression classifier, do feature selection (keeping the top 30%). It also tells the vectorizer to normalise using TFIDF. Importantly it filters the relations by argument types. It also has a sentence range of 1, meaning that it attempts to learn and predict relations that cross one sentence boundary.

The argument types are specified in the file passed to --relationDescriptions. This is a three column file with the first column being the name of relation, and the next two being acceptable argument types. This filtering works only on the input used to train and not necessarily on the output stage. Therefore final filtering should still be applied.

### Modification Extraction

We do the final extraction stage for modification that works similarly to the other extractors.

```shell
$python $verseDir/core/ModificationExtractor.py --trainingFile trainOrig.orig --testingFile relations.verse --outFile modSpeculation.verse --parameters "classifier:LogisticRegression ; threshold:0.2 ; featureChoice:ngrams" --modificationDescriptions $verseDir/BioNLP16-ST/GE4_auxFiles/mod.speculation
```

Again the --parameters option works in the same way to the other extractors. This time we use a logistic regression classifier with a specific threshold of 0.2. Using a lower threshold reduces the required probability for a prediction to be made, likely lowering false negatives but increasing false positives. The modificationDescriptions file is a simple file that names the modification(s) to be predicted.

If there is the possibility of an event having more than one modification (i.e. negation AND speculation), then multiple rounds of modification extractor should be run. Further ones (like below) should use the --mergeWithExisting flag so that existing modifications are not removed.

```shell
$python $verseDir/core/ModificationExtractor.py --trainingFile $trainOrig --testingFile modSpeculation.verse --outFile modSpeculationNegation.verse --parameters "classifier:LogisticRegression ; threshold:0.2; featureChoice:ngrams" --modificationDescriptions $verseDir/BioNLP16-ST/GE4_auxFiles/mod.negation --mergeWithExisting
```

### Filtering

The resulting predictions should be filtered to remove any relations of incorrect types, entities that aren't associated with relations and modifications of removed entities.

```shell
$python $verseDir/utils/Filter.py --relationFilters $verseDir/BioNLP16-ST/GE4_auxFiles/rel.filters --modificationFilters $verseDir/BioNLP16-ST/GE4_auxFiles/mod.filters --inFile modSpeculationNegation.verse --outFile filtered.verse
```

The filter files give the expected types for relations and modifications

### Export

With the predictions complete, we can now export back to the JSON format.

```shell
triggerTypes="Acetylation,Binding,Deacetylation,Gene_expression,Localization,Negative_regulation,Phosphorylation,Positive_regulation,Protein_catabolism,Protein_modification,Regulation,Transcription,Ubiquitination"
mkdir json
$python $verseDir/utils/ExportToJSON.py --inFile modSpeculationNegation.verse --outDir json --triggerTypes "$triggerTypes" --origDir bionlp-st-ge-2016-test-proteins
```

This takes in the original directory (--origDir) for the raw text and the entity types that should be used as event triggers (--triggerTypes as a comma-delimited list)
