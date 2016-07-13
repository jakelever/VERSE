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
		if triggerid in sentence.predictedEntityLocs:
			return sentenceid,sentence.predictedEntityLocs[triggerid]
	raise RuntimeError('Unable to find location of event trigger ID ('+triggerid+') in sentences')
	
def findArgumentTrigger(sentenceData,triggerid):
	for sentenceid, sentence in enumerate(sentenceData):
		if triggerid in sentence.knownEntityLocs:
			return sentenceid,sentence.knownEntityLocs[triggerid]
	raise RuntimeError('Unable to find location of argument trigger ID ('+triggerid+') in sentences')

def findTrigger(sentenceData,triggerid):
	for sentenceid, sentence in enumerate(sentenceData):
		if triggerid in sentence.predictedEntityLocs:
			return sentenceid,sentence.predictedEntityLocs[triggerid]
		if triggerid in sentence.knownEntityLocs:
			return sentenceid,sentence.knownEntityLocs[triggerid]
	raise RuntimeError('Unable to find location of trigger ID ('+triggerid+') in sentences')


def generateModificationExamples(sentenceAndEventData,targetModifications={}):

	examples = []
	classes = []
	
	# Let's first try to learn the event triggers (ignore this for trigger-less events)
	for filename in sentenceAndEventData:
			
		(sentenceData,relations,modifiers) = sentenceAndEventData[filename]

		positiveCases = {}
		for modifierid,(modifiertype,entityid) in modifiers.iteritems():
			if not entityid[0] == 'E':
				print "WARNING: Found modifier on non event denotations"
				print modifierid,modifiertype,entityid
				continue

			#sentenceid,locs = findEventTrigger(entityid)
			#positiveCases.add((sentenceid,locs))
			if modifiertype in targetModifications:
				positiveCases[entityid] = targetModifications[modifiertype]
		
		positiveCasesProcessed = []
		# Now we go through all sentences and create examples for all possible token combinations
		# Then check if any are already marked as positive and add to the appropriate list of examples
		for sentenceid,sentence in enumerate(sentenceData):
			tokenCount = len(sentence.tokens)
			for eventid in sentence.predictedEntityLocs:
				locs = sentence.predictedEntityLocs[eventid]
				type = sentence.predictedEntityTypes[eventid]
					
				example = Example(filename, sentenceData, arg1_sentenceid=sentenceid, arg1_locs=locs)
				examples.append(example)
				
				exampleClass = 0

				key = eventid
				if key in positiveCases:
					exampleClass = positiveCases[key]
					positiveCasesProcessed.append(key)
					#print "WOOOOO!!!! Positive added"
				classes.append(exampleClass)
						
			#print filename
		for key in positiveCases:
			if not key in positiveCasesProcessed:
				raise RuntimeError( 'WARNING: Unprocessed modification found: %s in file: %s' % (str(key), filename) )
					
	
	#for c,e in zip(classes,examples):
	#	print c,e
	#sys.exit(0)
	
	return classes, examples

def createModificationClassifier(sentenceAndEventData,targetModifications,parameters=None):
	classes,examples = generateModificationExamples(sentenceAndEventData,targetModifications)
	assert min(classes) == 0, "Expecting negative cases in modification examples"
	assert len(classes) > 0, "Expecting greater than zero classes & examples"

	if max(classes) == 0:
		print "WARNING: No modifications found. Are you sure that all events are triggerless?"
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
	parser = argparse.ArgumentParser(description='VERSE Modification Extraction tool')

	parser.add_argument('--trainingFile', required=True, type=str, help='Parsed-text file containing the training data')
	parser.add_argument('--testingFile', required=True, type=str, help='Parsed-text file containing the test data to predict modifications for')
	parser.add_argument('--modificationDescriptions', required=True, type=str, help='Description file containing list of modification types to predict')
	parser.add_argument('--mergeWithExisting', action='store_true',  help='Whether to keep existing modifications in testingFile')
	parser.add_argument('--parameters', type=str, help='Parameters to use for feature construction, selection and classification')
	parser.add_argument('--outFile', type=str, help='Output filename for data with predicted modifications')
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

	targetModifications = []
	with open(args.modificationDescriptions,'r') as f:
		for line in f:
			targetModifications.append(line.strip())

	targetModificationsToIDs = { event:i+1 for i,event in enumerate(targetModifications) }
	
	print "-"*30
	for i,targetModification in enumerate(targetModifications):
		print i, targetModification
	print "-"*30

	trigVec,trigFS,trigClf = None,None,None
	_,trigVec,trigFS,trigClf = createModificationClassifier(trainingSentenceAndEventData,targetModificationsToIDs,parameters)

	with open(args.testingFile, 'r') as f:
		testingSentenceAndEventData = pickle.load(f)
	print "Loaded " + args.testingFile
	
	if not args.mergeWithExisting:
		print "Blanking test data..."
		for filename in testingSentenceAndEventData:
			(sentenceData,relations,modifications) = testingSentenceAndEventData[filename]
			modifications = {}
			testingSentenceAndEventData[filename] = (sentenceData,relations,modifications)

	potentialEvents = {}
		
	print "generateTriggerExamples..."
	_,tExamples = generateModificationExamples(testingSentenceAndEventData,targetModificationsToIDs)

	assert len(tExamples) > 0, "Expecting greater than zero examples from the test data"
	
	print "vectorize, trim and predict..."
	tVectors = trigVec.vectorize(tExamples)
	if trigFS is None:
		tPredictions = trigClf.predict(tVectors)
	else:
		tTrimmed = trigFS.transform(tVectors)
		tPredictions = trigClf.predict(tTrimmed)
	
	predictedModificationID = 1
	
	potentialEventsArgs = defaultdict(list)
	
	print tPredictions
	print "insert modification predictions into sentence data..."
	for p,example in zip(tPredictions,tExamples):
		if p != 0:
			modType = targetModifications[p-1]
			
			sentenceFilename = example.filename
			sentenceID,locs = example.arguments[0]

			sentence = testingSentenceAndEventData[sentenceFilename][0][sentenceID]
			modifications = testingSentenceAndEventData[sentenceFilename][2]

			entityID = None
			for tmpID,tmpLocs in sentence.predictedEntityLocs.iteritems():
				if tmpLocs == locs:
					entityID = tmpID
					break

			assert not entityID is None
			
			triggerIDTxt = "M%d" % predictedModificationID
			predictedModificationID += 1

			print "ADDING", triggerIDTxt, modType, entityID
			modifications[triggerIDTxt] = (modType,entityID)

			
	with open(args.outFile, 'w') as f:
		pickle.dump(testingSentenceAndEventData,f)
		
	print "Complete."
