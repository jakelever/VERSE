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

## What's in this repo?

- [core](core/) - The main tools for text processing and prediction
- [utils](utils/) - Utilities to filter the input and output of VERSE (e.g. for invalid relations) and also to export to various formats.
- [evaluation](evaluation/) - Scripts to evaluate the results of VERSE
- [BioNLP16-ST](BioNLP16-ST/) - Scripts to run VERSE with the correct settings for the entries to the different subtasks in the BioNLP'16 Shared Task.

