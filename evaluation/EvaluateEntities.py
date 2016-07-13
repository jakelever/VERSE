
import sys
import os

# Include core directory for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

import argparse
import pickle
from collections import defaultdict,Counter
from DataLoad import *

def compareEvents(gSentenceData,tSentenceData):
	assert len(gSentenceData) == len(tSentenceData)
		
	scores = defaultdict(Counter)
	for i in range(len(gSentenceData)):
		goldTypes,goldLocs = gSentenceData[i].predictedEntityTypes.values(),gSentenceData[i].predictedEntityLocs.values()
		assert len(goldTypes)==len(goldLocs)
		testTypes,testLocs = tSentenceData[i].predictedEntityTypes.values(),tSentenceData[i].predictedEntityLocs.values()
		assert len(testTypes)==len(testLocs)
		
		
		goldZipped = set(zip(goldTypes,map(tuple,goldLocs)))
		testZipped = set(zip(testTypes,map(tuple,testLocs)))
		
		merged = set(list(goldZipped) + list(testZipped))
		
		for m in merged:
			test = m in testZipped
			gold = m in goldZipped
			
			assert test or gold
		
			eventType = m[0]
			if not test:
				scores[eventType]['FN'] = scores[eventType]['FN'] + 1
			elif not gold:
				scores[eventType]['FP'] = scores[eventType]['FP'] + 1
			else:
				scores[eventType]['TP'] = scores[eventType]['TP'] + 1
			
			
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
	gSentenceData,_,_ = goldData
	tSentenceData,_,_ = testData
	
	eventScores = compareEvents(gSentenceData,tSentenceData)
	
	return eventScores

if __name__ == "__main__":
	argparser = argparse.ArgumentParser(description='Evaluation tool for entity extraction results')
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

