
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
		#print triggerid, sentence.eventTriggerLocs, sentence.argumentTriggerLocs
		if triggerid in sentence.eventTriggerLocs:
			return sentenceid,sentence.eventTriggerLocs[triggerid]
		if triggerid in sentence.argumentTriggerLocs:
			return sentenceid,sentence.argumentTriggerLocs[triggerid]
	raise RuntimeError('Unable to find location of trigger ID ('+triggerid+') in sentences')

def getType(sentenceData,id):
	sentenceid,locs = findTrigger(sentenceData,id)
	sentence = sentenceData[sentenceid]
	return sentence.locsToTriggerTypes[tuple(locs)]

# It's the main bit. Yay!
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Removes entities, relations and modifications that are to be predicted')

	parser.add_argument('--inPickle', required=True, type=str, help='')
	parser.add_argument('--outPickle', required=True, type=str, help='')

	parser.add_argument('--rel_filters', required=True, type=str, help='')
	parser.add_argument('--mod_filters', required=True, type=str, help='')
	
	args = parser.parse_args()

	acceptedRelations = set()
	with open(args.rel_filters) as f:
		for line in f:
			relName,arg1,arg2 = line.strip().split('\t')
			r = (relName,arg1,arg2)
			acceptedRelations.add(r)
	
	acceptedModifications = set()
	with open(args.mod_filters) as f:
		for line in f:
			modName,arg1 = line.strip().split('\t')
			m = (modName,arg1)
			acceptedModifications.add(m)

	with open(args.inPickle, 'r') as f:
		data = pickle.load(f)
	print "Loaded " + args.inPickle
	
	print "Blanking predicted data..."
	for filename in data:
		(sentenceData,relations,modifications) = data[filename]
		#for s in sentenceData:
		#	s.eventTriggerLocs = {}
		#	s.eventTriggerTypes = {}
		#	s.refreshTakenLocs()
		#	s.invertTriggers()

		filteredRelations =  []
		seenIDs = set()
		for (relName,id1,id2) in relations:
			type1 = getType(sentenceData,id1)
			type2 = getType(sentenceData,id2)
			if (relName,type1,type2) in acceptedRelations:
				filteredRelations.append((relName,id1,id2))
				seenIDs.add(id1)
				seenIDs.add(id2)
			else:
				print "Skipping relation: ", (relName,type1,type2)

		for s in sentenceData:
			newLocs,newTypes = {},{}
			for id in s.eventTriggerLocs:
				if id in seenIDs:
					newLocs[id] = s.eventTriggerLocs[id]
					newTypes[id] = s.eventTriggerTypes[id]
				else:
					"Skipping entity: ", id
			s.eventTriggerLocs = newLocs
			s.eventTriggerTypes = newTypes
			s.refreshTakenLocs()
			s.invertTriggers()

		filteredModifications = {}
		for modid,(modtype,entityid) in modifications.iteritems():
			if not entityid in seenIDs:
				print "Skipping modification: ", (modtype,entityid)
				continue

			entitytype = getType(sentenceData,entityid)
			if (modtype,entitytype) in acceptedModifications:
				filteredModifications[modid] = (modtype,entityid)
			else:
				print "Skipping modification: ", (modtype,entitytype)

		data[filename] = (sentenceData,filteredRelations,filteredModifications)

			
	with open(args.outPickle, 'w') as f:
		pickle.dump(data,f)
		
	print "Complete."
