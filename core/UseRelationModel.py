import sys
import fileinput
import argparse
import time
import itertools
import pickle
import random
import codecs
from collections import defaultdict
from sklearn import svm
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import DictVectorizer
from scipy.sparse import coo_matrix, hstack, vstack
import numpy as np
import json

from ClassifierStuff import *
from SentenceModel import *

from CandidateBuilder import generateRelationCandidates

# It's the main bit. Yay!
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='VERSE Relation Extraction tool')

	parser.add_argument('--modelFile', required=True, type=str, help='')
	parser.add_argument('--testingFile', required=True, type=str, help='Parsed-text file containing the test data to predict modifications for')
	parser.add_argument('--outFile', type=str, help='Output filename for data with predicted modifications')
	args = parser.parse_args()

	with open(args.modelFile) as f:
		model = pickle.load(f)
	
	parameters = model['parameters'];
	targetRelations = model['targetRelations'];
	targetRelationsToIDs = model['targetRelationsToIDs'];
	targetArguments = model['targetArguments'];
	
	argVec = model['argVec'];
	argFS = model['argFS'];
	argClf = model['argClf'];
	
	sentenceRange = 0
	if "sentenceRange" in parameters:
		sentenceRange = int(parameters["sentenceRange"])
		
	doFiltering = False
	if 'doFiltering' in parameters and parameters['doFiltering'] == 'True':
		doFiltering = True

	with open(args.testingFile, 'r') as f:
		testingSentenceAndEventData = pickle.load(f)
	print "Loaded " + args.testingFile

	# Empty the test data of any existing predictions (in case we load the wrong test file)
	for filename in testingSentenceAndEventData:
		(sentenceData,relations,modifiers) = testingSentenceAndEventData[filename]
		# Empty relations
		relations = []
		
		testingSentenceAndEventData[filename] = (sentenceData,relations,modifiers)
		
	print "generate Argument Examples..."
	_,aExamples,aTypes = generateRelationCandidates(testingSentenceAndEventData,targetRelationsToIDs,targetArguments,sentenceRange,doFiltering)
	
	print "vectorize, trim and predict..."

	aVectors = argVec.vectorize(aExamples)
	if not argFS is None:
		aVectors = argFS.transform(aVectors)
	aVectors = coo_matrix(aVectors)

	aPredictions = argClf.predict(aVectors)
	aProbs = argClf.predict_proba(aVectors)
	probColumns = { c:i for i,c in enumerate(argClf.classes_) }

	#predictedEventID = 1
	predictedTriggerID = 1000
	
	predictedEventIDPerFile = Counter()
	
	for i,(p,example) in enumerate(zip(aPredictions,aExamples)):
		if p != 0:
			relType = targetRelations[p-1]
			
			#eventType = thisRelation[1]
			#argTypes = thisRelation[2:]
			#assert len(argTypes) == 2, "Only processing binary relations for triggerless events"

			#eventType = thisRelation[0]
			
			sentenceFilename = example.filename
			sentenceID1,arg1Locs = example.arguments[0]
			sentenceID2,arg2Locs = example.arguments[1]


			sentence1 = testingSentenceAndEventData[sentenceFilename][0][sentenceID1]
			sentence2 = testingSentenceAndEventData[sentenceFilename][0][sentenceID2]

			sentence1.invertTriggers()
			sentence2.invertTriggers()

			arg1ID = sentence1.locsToTriggerIDs[tuple(arg1Locs)]
			arg2ID = sentence2.locsToTriggerIDs[tuple(arg2Locs)]

			type1ID = sentence1.locsToTriggerTypes[tuple(arg1Locs)]
			type2ID = sentence2.locsToTriggerTypes[tuple(arg2Locs)]

			#relType = typeLookup[type1ID]

			relations = testingSentenceAndEventData[sentenceFilename][1]
			
			prob = aProbs[i,probColumns[p]]

			newR = (relType,arg1ID,arg2ID,prob)
			#print "ADDING", newR
			relations.append(newR)
			#print "TEST",sentenceFilename,sentenceID1,sentenceID2,arg1Locs,arg2Locs,relType


	with open(args.outFile, 'w') as f:
		pickle.dump(testingSentenceAndEventData,f)
				
	print "Complete."
