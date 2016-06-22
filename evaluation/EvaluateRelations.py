
import sys
import os

# Include core directory for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

import argparse
import pickle
from collections import defaultdict,Counter
from DataLoad import *

def findTrigger(sentenceData,triggerid):
	for sentenceid, sentence in enumerate(sentenceData):
		if triggerid in sentence.eventTriggerLocs:
			return sentenceid,sentence.eventTriggerLocs[triggerid]
		if triggerid in sentence.argumentTriggerLocs:
			return sentenceid,sentence.argumentTriggerLocs[triggerid]
	raise RuntimeError('Unable to find location of trigger ID ('+triggerid+') in sentences')


def compareRelations(gRelations,tRelations,gSentenceData,tSentenceData,targetRelations):
	noFilter = (len(targetRelations) == 0)
	
	goldR = set()
	for relType,id1,id2 in gRelations:
		sentenceid1,locs1 = findTrigger(gSentenceData,id1)
		sentenceid2,locs2 = findTrigger(gSentenceData,id2)
		r = (relType,sentenceid1,tuple(locs1),sentenceid2,tuple(locs2))
		goldR.add(r)
		
	testR = set()
	for relType,id1,id2 in tRelations:
		sentenceid1,locs1 = findTrigger(tSentenceData,id1)
		sentenceid2,locs2 = findTrigger(tSentenceData,id2)
		r = (relType,sentenceid1,tuple(locs1),sentenceid2,tuple(locs2))
		testR.add(r)

	merged = set(list(goldR) + list(testR))

	scores = defaultdict(Counter)
	for m in merged:
		relType,sentenceid1,locs1,sentenceid2,locs2 = m

		test = m in testR
		gold = m in goldR
		
		assert test or gold

		scoreType = None
		if not test:
			type1 = gSentenceData[sentenceid1].locsToTriggerTypes[locs1]
			type2 = gSentenceData[sentenceid2].locsToTriggerTypes[locs2]
			scoreType = 'FN'
		elif not gold:
			type1 = tSentenceData[sentenceid1].locsToTriggerTypes[locs1]
			type2 = tSentenceData[sentenceid2].locsToTriggerTypes[locs2]
			scoreType = 'FP'
		else:
			type1 = gSentenceData[sentenceid1].locsToTriggerTypes[locs1]
			type2 = gSentenceData[sentenceid2].locsToTriggerTypes[locs2]
			scoreType = 'TP'

		key = (relType,type1,type2)
		if noFilter:
			scores[relType][scoreType] = scores[relType][scoreType] + 1
		elif key in targetRelations:
			txtKey = "|".join(key)
			scores[txtKey][scoreType] = scores[txtKey][scoreType] + 1
			
			
	return scores
	
def combineCounters(c1,c2):
	newScores = defaultdict(Counter)
	combinedKeys1 = list(set(c1.keys() + c2.keys()))
	for k1 in combinedKeys1:
		combinedKeys2 = list(set(c1[k1].keys() + c2[k1].keys()))
		for k2 in combinedKeys2:
			newScores[k1][k2] = c1[k1][k2] + c2[k1][k2]
	return newScores
	
def compare(goldData,testData,targetRelations):
	gSentenceData,gRelations,_ = goldData
	tSentenceData,tRelations,_ = testData
	
	relScores = compareRelations(gRelations,tRelations,gSentenceData,tSentenceData,targetRelations)

	return relScores

if __name__ == "__main__":
	argparser = argparse.ArgumentParser(description='Evaluation tool for entity extraction results')
	argparser.add_argument('--goldPickle', required=True, type=str, help='Directory containing gold files')
	argparser.add_argument('--testPickle', required=True, type=str, help='Directory containing test files')
	argparser.add_argument('--rel_descriptions', type=str, help='')
	args = argparser.parse_args()
	
	with open(args.goldPickle, 'r') as f:
		goldData = pickle.load(f)
	with open(args.testPickle, 'r') as f:
		testData = pickle.load(f)

	targetRelations,targetArguments = set(),set()
	if args.rel_descriptions:
		with open(args.rel_descriptions,'r') as f:
			for line in f:
				name,type1,type2 = line.strip().split('\t')
				targetRelations.add((name,type1,type2))
				targetArguments.add((type1,type2))
	
	assert set(goldData.keys()) == set(testData.keys()), "Mismatch between data in gold data and test data"
	
	allScores = defaultdict(Counter)
	for filename in goldData:
		theseScores = compare(goldData[filename],testData[filename],targetRelations)
			
		allScores = combineCounters(allScores, theseScores)
	
	tp,fp,fn,partial = 0,0,0,0
	
	sortedEventTypes = sorted(allScores.keys())
	for eventType in sortedEventTypes:
		scores = allScores[eventType]
		tp = tp + scores['TP']
		fp = fp + scores['FP']
		fn = fn + scores['FN']
		partial = partial + scores['Partial']
		recall,precision,f1score = 0.0,0.0,0.0
		if scores['TP'] > 0:
			recall = scores['TP'] / float(scores['TP'] + scores['FN'])
			precision = scores['TP'] / float(scores['TP'] + scores['FP'])
			f1score = 2*(precision*recall)/(precision+recall)
		
		print "TP=%d\tFP=%d\tFN=%d\tPartial=%d\tR=%.3f\tP=%.3f\tF1=%.3f\t%s" % (scores['TP'],scores['FP'],scores['FN'],scores['Partial'],recall,precision,f1score,eventType)

		
	recall,precision,f1score,f0point1score,f10score = 0.0,0.0,0.0,0.0,0.0
	if tp > 0:
		recall = tp / float(tp+fn)
		precision = tp / float(tp + fp)
		f1score = 2*(precision*recall)/(precision+recall)
		beta = 0.1
		f0point1score = (1+beta*beta)*(precision*recall)/(beta*beta*precision+recall)
		beta = 10
		f10score = (1+beta*beta)*(precision*recall)/(beta*beta*precision+recall)

	print
	print "Summary\tR=%.3f\tP=%.3f\tF1=%.3f\tF0.1=%.3f\tF10=%.3f" % (recall,precision,f1score,f0point1score,f10score)

