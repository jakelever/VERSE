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

from CandidateBuilder import generateRelationCandidates,findTrigger

def createRelationClassifier(sentenceAndEventData,targetRelations,targetArguments,parameters=None,generateClassifier=True,sentenceRange=0,doFiltering=False):
	classes,examples,relTypes = generateRelationCandidates(sentenceAndEventData,targetRelations,targetArguments,sentenceRange,doFiltering)
	assert min(classes) == 0, "Expecting negative cases in relation examples"
	assert max(classes) > 0, "Expecting positive cases in relation examples"
	
	vectors,vectorizer,featureSelector = buildVectorizer(classes,examples,parameters)

	classifier = None
	if generateClassifier:
		classifier = buildClassifierFromVectors(classes,vectors,parameters)

	data = (classes,examples,vectors,relTypes)
	return data,vectorizer,featureSelector,classifier

# It's the main bit. Yay!
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='VERSE Relation Extraction tool')

	parser.add_argument('--trainingFile', required=True, type=str, help='Parsed-text file containing the training data')
	parser.add_argument('--relationDescriptions', required=True, type=str, help='Description file containing list of relation types with arguments to predict')
	parser.add_argument('--parameters', type=str, help='Parameters to use for feature construction, selection and classification')
	parser.add_argument('--modelFile', type=str, help='Output filename for data with predicted modifications')
	args = parser.parse_args()

	parameters = {}
	if args.parameters:
		for arg in args.parameters.split(';'):
			name,value = arg.strip().split(":")
			parameters[name.strip()] = value.strip()
			
	sentenceRange = 0
	if "sentenceRange" in parameters:
		sentenceRange = int(parameters["sentenceRange"])
	
	trainFilename = args.trainingFile
	with open(trainFilename, 'r') as f:
		trainingSentenceAndEventData = pickle.load(f)
	print "Loaded " + trainFilename

	tmpTargetRelations = set()
	for filename,data in trainingSentenceAndEventData.iteritems():
		sentenceData = data[0]
		relations = data[1]

		for (relName,id1,id2) in relations:
			sentenceid1,locs1 = findTrigger(sentenceData,id1)
			sentenceid2,locs2 = findTrigger(sentenceData,id2)
			type1 = sentenceData[sentenceid1].locsToTriggerTypes[tuple(locs1)]
			type2 = sentenceData[sentenceid2].locsToTriggerTypes[tuple(locs2)]
			tmpTargetRelations.add((relName,type1,type2))

	print "#"*30
	for relName,type1,type2 in tmpTargetRelations:
		print "%s\t%s\t%s" % (relName,type1,type2)
	print "#"*30

	doFiltering = False
	if 'doFiltering' in parameters and parameters['doFiltering'] == 'True':
		doFiltering = True

	#targetRelations = []
	targetRelations,targetArguments = set(),set()
	#typeLookup = {}
	with open(args.relationDescriptions,'r') as f:
		for line in f:
			nameAndArgs,type1,type2 = line.strip().split('\t')

			# Pull out the name of arguments and sort by the argument names
			nameAndArgsSplit = nameAndArgs.split(';')

			# Basically don't do anything if we aren't given the argument names
			if len(nameAndArgsSplit) == 1:
				targetRelations.add(tuple(nameAndArgsSplit))
				targetArguments.add((type1,type2))
			else: # Or do sort by argument names (if they are provided)
				relName,argName1,argName2 = nameAndArgs.split(';')
				relArgs = [(argName1,type1),(argName2,type2)]
				relArgs = sorted(relArgs)
				
				targetRelations.add((relName,relArgs[0][0],relArgs[1][0]))
				targetArguments.add((relArgs[0][1],relArgs[1][1]))

	targetRelations = list(targetRelations)
	targetRelations = sorted(targetRelations)

	targetRelationsToIDs = { arg:i+1 for i,arg in enumerate(targetRelations) }

	print "-"*30
	for targetRelation in targetRelations:
		print targetRelation
	print "-"*30
	for targetArgument in targetArguments:
		print targetArgument
	print "-"*30
	
	relData,argVec,argFS,argClf = createRelationClassifier(trainingSentenceAndEventData,targetRelationsToIDs,targetArguments,parameters,True,sentenceRange,doFiltering)

	model = {}
	
	model['parameters'] = parameters;
	model['targetRelations'] = targetRelations;
	model['targetRelationsToIDs'] = targetRelationsToIDs;
	model['targetArguments'] = targetArguments;
	
	model['argVec'] = argVec;
	model['argFS'] = argFS;
	model['argClf'] = argClf;
	
	with open(args.modelFile,'w') as f:
		pickle.dump(model,f)
