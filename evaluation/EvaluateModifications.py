
import sys
import os

# Include core directory for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

import argparse
import pickle
from collections import defaultdict,Counter
from DataLoad import *
from SentenceModel import *

def findTrigger(sentenceData,triggerid):
	for sentenceid, sentence in enumerate(sentenceData):
		if triggerid in sentence.predictedEntityLocs:
			return sentenceid,sentence.predictedEntityLocs[triggerid]
		if triggerid in sentence.knownEntityLocs:
			return sentenceid,sentence.knownEntityLocs[triggerid]
	raise RuntimeError('Unable to find location of trigger ID ('+triggerid+') in sentences')

def compareModifications(gModifications,tModifications,gSentenceData,tSentenceData):
	#goldM = set(gModifications.values())
	#testM = set(tModifications.values())
	
	goldM = set()
	for type,entityid in gModifications.values():
		sentenceid,locs = findTrigger(gSentenceData,entityid)
		m = (type,sentenceid,tuple(locs))
		goldM.add(m)

	testM = set()
	for type,entityid in tModifications.values():
		sentenceid,locs = findTrigger(tSentenceData,entityid)
		m = (type,sentenceid,tuple(locs))
		testM.add(m)
	
	#merged = set(gModifications.values() + tModifications.values())

	merged = set(list(goldM) + list(testM))
	
	scores = defaultdict(Counter)
	for m in merged:
		test = m in testM 
		gold = m in goldM
		
		assert test or gold
	
		modType = m[0]
		if not test:
			scores[modType]['FN'] = scores[modType]['FN'] + 1
		elif not gold:
			scores[modType]['FP'] = scores[modType]['FP'] + 1
		else:
			scores[modType]['TP'] = scores[modType]['TP'] + 1
			
	return scores
	
def combineCounters(c1,c2):
	newScores = defaultdict(Counter)
	combinedKeys1 = list(set(c1.keys() + c2.keys()))
	for k1 in combinedKeys1:
		combinedKeys2 = list(set(c1[k1].keys() + c2[k1].keys()))
		for k2 in combinedKeys2:
			newScores[k1][k2] = c1[k1][k2] + c2[k1][k2]
	return newScores
	
def compare(goldData,testData):
	gSentenceData,_,gModifications = goldData
	tSentenceData,_,tModifications = testData
	
	modScores = compareModifications(gModifications,tModifications,gSentenceData,tSentenceData)

	return modScores

if __name__ == "__main__":
	argparser = argparse.ArgumentParser(description='Evaluation tool for modification extraction results')
	argparser.add_argument('--goldFile', required=True, type=str, help='File containing gold data')
	argparser.add_argument('--testFile', required=True, type=str, help='File containing test data')
	args = argparser.parse_args()
	
	with open(args.goldFile, 'r') as f:
		goldData = pickle.load(f)
	with open(args.testFile, 'r') as f:
		testData = pickle.load(f)
	
	assert set(goldData.keys()) == set(testData.keys()), "Mismatch between data in gold data and test data"
	
	allScores = defaultdict(Counter)
	for filename in goldData:
		theseScores = compare(goldData[filename],testData[filename])
			
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

