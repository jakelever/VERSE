
import sys
import os

# Include core directory for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

import fileinput
import argparse
import time
import itertools
import pickle
import random
import codecs
from collections import defaultdict

from SentenceModel import *

def findTrigger(sentenceData,triggerid):
	for sentenceid, sentence in enumerate(sentenceData):
		#print triggerid, sentence.predictedEntityLocs, sentence.knownEntityLocs
		if triggerid in sentence.predictedEntityLocs:
			return sentenceid,sentence.predictedEntityLocs[triggerid]
		if triggerid in sentence.knownEntityLocs:
			return sentenceid,sentence.knownEntityLocs[triggerid]
	raise RuntimeError('Unable to find location of trigger ID ('+triggerid+') in sentences')

def getType(sentenceData,id):
	sentenceid,locs = findTrigger(sentenceData,id)
	sentence = sentenceData[sentenceid]
	return sentence.locsToTriggerTypes[tuple(locs)]

# It's the main bit. Yay!
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Removes entities, relations and modifications that don't match expected types for relations and modifications")

	parser.add_argument('--inFile', required=True, type=str, help='File to be filtered')
	parser.add_argument('--outFile', required=True, type=str, help='Filename for output filtered file')

	parser.add_argument('--relationFilters', required=True, type=str, help='File containing tab-delimited description of acceptable relations (name,type1,type2)')
	parser.add_argument('--modificationFilters', type=str, help='File containing name of acceptable modifications with type of entity')
	
	args = parser.parse_args()
	
	with open(args.inFile, 'r') as f:
		data = pickle.load(f)
	print "Loaded " + args.inFile
	
	# Collect all the types (for use with possible wildcards)
	allEntityTypes = set()
	for filename in data:
		sentenceData,_,_ = data[filename]
		for sentence in sentenceData:
			allEntityTypes.update(sentence.predictedEntityTypes.values())
			allEntityTypes.update(sentence.knownEntityTypes.values())

	acceptedRelations = set()
	with open(args.relationFilters) as f:
		for line in f:
			relDetails,arg1Txt,arg2Txt = line.strip().split('\t')
			relDetails = relDetails.split(";")
			relArgNames = relDetails[1:]
	
			# Organise arguments in alphabetical order
			relStuff = list(zip(relArgNames,[arg1Txt,arg2Txt]))
			relStuff = sorted(relStuff)

			sortedDetails = (relDetails[0],relStuff[0][0],relStuff[1][0])
			arg1Txt,arg2Txt = relStuff[0][1],relStuff[1][1]

			if arg1Txt == '*':
				arg1s = allEntityTypes
			else:
				arg1s = set(arg1Txt.split('|'))
			if arg2Txt == '*':
				arg2s = allEntityTypes
			else:
				arg2s = set(arg2Txt.split('|'))
			
			for arg1,arg2 in itertools.product(arg1s,arg2s):
				r = (sortedDetails,arg1,arg2)
				acceptedRelations.add(r)
	
	doFilterModifications = False
	acceptedModifications = set()
	if args.modificationFilters:
		doFilterModifications = True
		with open(args.modificationFilters) as f:
			for line in f:
				modName,arg1 = line.strip().split('\t')
				m = (modName,arg1)
				acceptedModifications.add(m)
	
	print "Blanking predicted data..."
	for filename in data:
		(sentenceData,relations,modifications) = data[filename]
		#for s in sentenceData:
		#	s.predictedEntityLocs = {}
		#	s.predictedEntityTypes = {}
		#	s.refreshTakenLocs()
		#	s.invertTriggers()

		filteredRelations =  []
		seenIDs = set()
		for (relName,id1,id2,prob) in relations:
			type1 = getType(sentenceData,id1)
			type2 = getType(sentenceData,id2)
			if (relName,type1,type2) in acceptedRelations:
				filteredRelations.append((relName,id1,id2,prob))
				seenIDs.add(id1)
				seenIDs.add(id2)
			else:
				print "Skipping relation: ", (relName,type1,type2,prob)

		for s in sentenceData:
			newLocs,newTypes = {},{}
			for id in s.predictedEntityLocs:
				if id in seenIDs:
					newLocs[id] = s.predictedEntityLocs[id]
					newTypes[id] = s.predictedEntityTypes[id]
				else:
					"Skipping entity: ", id
			s.predictedEntityLocs = newLocs
			s.predictedEntityTypes = newTypes
			s.refreshTakenLocs()
			s.invertTriggers()

		filteredModifications = {}
		for modid,(modtype,entityid) in modifications.iteritems():
			if not entityid in seenIDs:
				print "Skipping modification: ", (modtype,entityid)
				continue

			entitytype = getType(sentenceData,entityid)
			if doFilterModifications and (modtype,entitytype) in acceptedModifications:
				filteredModifications[modid] = (modtype,entityid)
			else:
				print "Skipping modification: ", (modtype,entitytype)

		data[filename] = (sentenceData,filteredRelations,filteredModifications)

			
	with open(args.outFile, 'w') as f:
		pickle.dump(data,f)
		
	print "Complete."
