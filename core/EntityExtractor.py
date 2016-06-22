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

from ClassifierStuff import *
from SentenceModel import *

def findEventTrigger(sentenceData,triggerid):
	for sentenceid, sentence in enumerate(sentenceData):
		if triggerid in sentence.eventTriggerLocs:
			return sentenceid,sentence.eventTriggerLocs[triggerid]
	raise RuntimeError('Unable to find location of event trigger ID ('+triggerid+') in sentences')
	
def findArgumentTrigger(sentenceData,triggerid):
	for sentenceid, sentence in enumerate(sentenceData):
		if triggerid in sentence.argumentTriggerLocs:
			return sentenceid,sentence.argumentTriggerLocs[triggerid]
	raise RuntimeError('Unable to find location of argument trigger ID ('+triggerid+') in sentences')

def findTrigger(sentenceData,triggerid):
	for sentenceid, sentence in enumerate(sentenceData):
		if triggerid in sentence.eventTriggerLocs:
			return sentenceid,sentence.eventTriggerLocs[triggerid]
		if triggerid in sentence.argumentTriggerLocs:
			return sentenceid,sentence.argumentTriggerLocs[triggerid]
	raise RuntimeError('Unable to find location of trigger ID ('+triggerid+') in sentences')


maxTriggerLength = None
positiveEntities = None
def generateTriggerExamples(sentenceAndEventData,targetEvents={}):
	global maxTriggerLength,positiveEntities

	examples = []
	classes = []
	
	if maxTriggerLength is None:
		# First off, let's find out how many tokens this trigger can possibly be
		# TODO: We need a way that this can be passed from the training data call to the test data call (so that they use the same)
		maxTriggerLength = 1
		positiveEntities = set()
		for filename in sentenceAndEventData:
			(sentenceData,relations,modifiers) = sentenceAndEventData[filename]

			for sentenceid,sentence in enumerate(sentenceData):
				tokenCount = len(sentence.tokens)
				for eventid in sentence.eventTriggerLocs:
					locs = sentence.eventTriggerLocs[eventid]
					type = sentence.eventTriggerTypes[eventid]
					if type in targetEvents:
						tokens = [ sentence.tokens[l].word for l in locs ]
						positiveEntities.add(tuple(tokens))
					maxTriggerLength = max(maxTriggerLength,len(locs))
		print "maxTriggerLength:",maxTriggerLength
		print positiveEntities

	# Let's first try to learn the event triggers (ignore this for trigger-less events)
	for filename in sentenceAndEventData:
			
		#print "FILENAME:",filename
			
		(sentenceData,relations,modifiers) = sentenceAndEventData[filename]

			
		# Now we go through all sentences and create examples for all possible token combinations
		# Then check if any are already marked as positive and add to the appropriate list of examples
		for sentenceid,sentence in enumerate(sentenceData):
			tokenCount = len(sentence.tokens)
			positiveEventTriggerLocs = {}
			for eventid in sentence.eventTriggerLocs:
				locs = sentence.eventTriggerLocs[eventid]
				type = sentence.eventTriggerTypes[eventid]
				tokens = [ sentence.tokens[l].word for l in locs ]
				if type in targetEvents:
					classid = targetEvents[type]
					positiveEventTriggerLocs[tuple(locs)] = classid
			positiveEventTriggerLocsProcessed = []
			#for eventTriggerID,argLocs in sentence.eventTriggerLocs.iteritems():
			#print positiveEventTriggerLocs
				
			# We're going to remove all argument locs
			possibleLocs = range(tokenCount)
			usedLocs = set()
			for argTriggerID,argLocs in sentence.argumentTriggerLocs.iteritems():
				usedLocs.update(argLocs)
				for loc in argLocs:
					if loc in possibleLocs:
						possibleLocs.remove(loc)
			
			#for triggerLength in range(1,maxTriggerLength+1):
			#	for locs in itertools.combinations(possibleLocs,triggerLength):

			#print "possibleLocs", possibleLocs
			for triggerLength in range(1,maxTriggerLength+1):
				for start in range(0,tokenCount-triggerLength):
					locs = range(start,start+triggerLength)
					locs = list(locs)
					overlapsArguments = any ( [ l in usedLocs for l in locs ] )
					if overlapsArguments:
						continue

					key = tuple(locs)
					tokens = [ sentence.tokens[l].word for l in locs ]
					if not tuple(tokens) in positiveEntities:
						continue
					
					example = Example(filename, sentenceData, arg1_sentenceid=sentenceid, arg1_locs=locs)
					examples.append(example)
					
					exampleClass = 0
					if key in positiveEventTriggerLocs:
						exampleClass = positiveEventTriggerLocs[key]
						positiveEventTriggerLocsProcessed.append(key)
						#print "WOOOOO!!!! Positive added"
					classes.append(exampleClass)
						
			#print filename
			for key in positiveEventTriggerLocs:
				if not key in positiveEventTriggerLocsProcessed:
					print 'WARNING: Unprocessed event trigger found: %s in file: %s, %d' % (str(key), filename, sentenceid)
					
	
	#for c,e in zip(classes,examples):
	#	print c,e
	
	return classes, examples

def createTriggerClassifier(sentenceAndEventData,targetEvents,parameters=None):
	classes,examples = generateTriggerExamples(sentenceAndEventData,targetEvents)
	assert min(classes) == 0, "Expecting negative cases in trigger examples"

	if max(classes) == 0:
		print "WARNING: No event triggers found. Are you sure that all events are triggerless?"
		return None,None,None,None
	
	vectors,vectorizer,featureSelector = buildVectorizer(classes,examples,parameters)
	classifier = buildClassifierFromVectors(classes,vectors,parameters)
	data = (classes,examples,vectors)
	return data,vectorizer,featureSelector,classifier
	
	
def saveCOOMatrixToFile(matrix,filename):
	with open(filename,'w') as f:
		f.write("%%sparse\t%d\t%d\n" % (matrix.shape[0],matrix.shape[1]))
		for row,col,data in zip(matrix.row,matrix.col,matrix.data):
			line = "%d\t%d\t%f" % (row,col,data)
			f.write(line + "\n")

def loadCOOMatrixFromFile(filename):
	rows,cols = -1,-1
	data = []
	matrix = None
	with open(filename,'r') as f:
		header = True
		for line in f:
			if header:
				_,r,c = line.split("\t")
				rows,cols = int(r),int(c)
				header = False
			else:
				x,y,value = line.split("\t")
				x,y,value = int(x),int(y),float(value)
				data.append((x,y,value))

	xs = [ x for x,y,value in data ]
	ys = [ y for x,y,value in data ]
	vals = [ value for x,y,value in data ]

	matrix = coo_matrix((vals,(xs,ys)),shape=(rows,cols))
	return matrix

def loadNumpyArrayFromFile(filename):
	return np.loadtxt(filename,comments='%')

def loadMatrixFromFile(filename):
	with open(filename,'r') as f:
		header = f.readline().strip().split("\t")
	type,dim1,dim2 = header
	#dim1,dim2 = int(dim1),int(dim2)
	print filename, type
	if type == "%sparse":
		return loadCOOMatrixFromFile(filename)
	elif type == "%dense":
		return loadNumpyArrayFromFile(filename)
	else:
		raise RuntimeError("Unknown type of matrix: %s" % type)
		
# It's the main bit. Yay!
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='VERSE entity extractor')

	parser.add_argument('--trainingPickle', required=True, type=str, help='')
	parser.add_argument('--testingPickle', required=True, type=str, help='')

	parser.add_argument('--entity_descriptions', required=True, type=str, help='')
	parser.add_argument('--mergeWithExistingEntities', action='store_true',  help='If existing entities exist in the testingPickle, they aren\'t removed, and are simply added to')

	parser.add_argument('--parameters', type=str, help='')
	parser.add_argument('--outPickle', type=str, help='')
	args = parser.parse_args()

	parameters = {}
	if args.parameters:
		for arg in args.parameters.split(';'):
			name,value = arg.strip().split(":")
			parameters[name.strip()] = value.strip()
			
	sentenceRange = 0
	if "sentenceRange" in parameters:
		sentenceRange = int(parameters["sentenceRange"])
	
	trainFilename = args.trainingPickle
	with open(trainFilename, 'r') as f:
		trainingSentenceAndEventData = pickle.load(f)
	print "Loaded " + trainFilename

	tmpTargetEntities = set()
	for filename,data in trainingSentenceAndEventData.iteritems():
		sentenceData = data[0]
		relations = data[1]

		for sentence in sentenceData:
			for id,type in sentence.eventTriggerTypes.iteritems():
				tmpTargetEntities.add(type)
	
	print tmpTargetEntities

	targetEntities = []
	with open(args.entity_descriptions,'r') as f:
		for line in f:
			targetEntities.append(line.strip())

	targetEntitiesToIDs = { event:i+1 for i,event in enumerate(targetEntities) }
	
	print "-"*30
	for i,targetEvent in enumerate(targetEntities):
		print i, targetEvent
	print "-"*30

	trigVec,trigFS,trigClf = None,None,None
	_,trigVec,trigFS,trigClf = createTriggerClassifier(trainingSentenceAndEventData,targetEntitiesToIDs,parameters)

	with open(args.testingPickle, 'r') as f:
		testingSentenceAndEventData = pickle.load(f)
	print "Loaded " + args.testingPickle
	
	if not args.mergeWithExistingEntities:
		print "Blanking test data..."
		for filename in testingSentenceAndEventData:
			(sentenceData,relations,modifiers) = testingSentenceAndEventData[filename]
			for s in sentenceData:
				s.eventTriggerLocs = {}
				s.eventTriggerTypes = {}
				s.refreshTakenLocs()
			testingSentenceAndEventData[filename] = (sentenceData,relations,modifiers)

	potentialEvents = {}
		
	print "generateTriggerExamples..."
	_,tExamples = generateTriggerExamples(testingSentenceAndEventData,targetEntitiesToIDs)
	
	print "vectorize, trim and predict..."
	tVectors = trigVec.vectorize(tExamples)
	if trigFS is None:
		tPredictions = trigClf.predict(tVectors)
	else:
		tTrimmed = trigFS.transform(tVectors)
		tPredictions = trigClf.predict(tTrimmed)
	
	predictedTriggerID = 1
	
	potentialEventsArgs = defaultdict(list)
	
	print tPredictions
	print "insert trigger predictions into sentence data..."
	for p,example in zip(tPredictions,tExamples):
		if p != 0:
			entityType = targetEntities[p-1]
			
			sentenceFilename = example.filename
			sentenceID,locs = example.arguments[0]
			
			triggerIDTxt = "EE%d" % predictedTriggerID
			predictedTriggerID = predictedTriggerID + 1
			
			#print "ADDING", sentenceID, triggerIDTxt, locs, entityType
			sentence = testingSentenceAndEventData[sentenceFilename][0][sentenceID]
			sentence.invertTriggers()
			sentence.refreshTakenLocs()
			
			locAlreadyUsed = tuple(locs) in sentence.takenLocs
			if args.mergeWithExistingEntities and locAlreadyUsed:
				print "Predicting existing location. Skipping..."
			elif locAlreadyUsed:
				raise RuntimeError("Entity location already used when trying to create new prediction")
			else:
				sentence.addEventTrigger(triggerIDTxt, locs, entityType)
			
			eventKey = (sentenceFilename,sentenceID,tuple(locs))
			assert not eventKey in potentialEvents
			
			potentialEvents[eventKey] = entityType
			# TODO: These modifications should maybe be done of a separate version for each argument type (or at least so that a "clean" version is used for classification each time)

			
	with open(args.outPickle, 'w') as f:
		pickle.dump(testingSentenceAndEventData,f)
		
	print "Complete."
