
import sys
import os

# Include core directory for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

import argparse
from collections import defaultdict,Counter
from DataLoad import *

def groupEventsAndRelations(denotations,relations):
	events = {}
	triggerless = {}
	for id,(typeName, positions, tokens) in denotations.iteritems():
		if id.startswith('E'): # It's an event trigger
			events[tuple(positions)] = {'EventType':typeName}
			
	for (relName, eventID, argID) in relations:
		eventName, argName1, argName2 = relName
		
		args = [(argName1,eventID),(argName2,argID)]
		args = sorted(args)
		
		arg1Positions = tuple(denotations[args[0][1]][1])
		arg2Positions = tuple(denotations[args[1][1]][1])
		
		key = (eventName, args[0][0], arg1Positions, args[1][0], arg2Positions)
		triggerless[key] = True
			
	return events, triggerless
	
def groupModifications(denotations, modifications):
	mods = {}
	for id,(modType,modSubject) in modifications.iteritems():
		positions = tuple(denotations[modSubject][1])
		key = (modType,positions)
		mods[key] = True
	return mods
	
def compareModifications(gMods,tMods):
	combinedKeys = list(set(gMods.keys() + tMods.keys()))
			
	scores = defaultdict(Counter)
	for k in combinedKeys:
		gold = k in gMods
		test = k in tMods
		
		assert gold or test
		
		modType = k[0]
		if gold and test:
			scores[modType]['TP'] = scores[modType]['TP'] + 1
		elif gold:
			scores[modType]['FN'] = scores[modType]['FN'] + 1
		elif test:
			scores[modType]['FP'] = scores[modType]['FP'] + 1
		
	return scores

def compareEvents(gEvents,tEvents):
	combinedKeys = list(set(gEvents.keys() + tEvents.keys()))
	for k in combinedKeys:
		if not k in gEvents:
			gEvents[k] = None
		if not k in tEvents:
			tEvents[k] = None
	
	scores = defaultdict(Counter)
	for k in combinedKeys:
		gold = gEvents[k]
		test = tEvents[k]
		matching = (gold == test)
		
		assert not (gold is None and test is None)
		
		if test is None:
			eventType = gold['EventType']
			scores[eventType]['FN'] = scores[eventType]['FN'] + 1
		elif gold is None:
			eventType = test['EventType']
			scores[eventType]['FP'] = scores[eventType]['FP'] + 1
		elif matching:
			eventType = test['EventType']
			scores[eventType]['TP'] = scores[eventType]['TP'] + 1
		elif gold['EventType'] == test['EventType']:
			eventType = test['EventType']
			scores[eventType]['Partial'] = scores[eventType]['Partial'] + 1
		else:
			eventType = 'EventTypeDisagreement'
			scores[eventType]['Partial'] = scores[eventType]['Partial'] + 1
			
			
	return scores
	
def compareRelations(gTriggerless,tTriggerless):
	combinedKeys = list(set(gTriggerless.keys() + tTriggerless.keys()))
			
	scores = defaultdict(Counter)
	for k in combinedKeys:
		gold = k in gTriggerless
		test = k in tTriggerless
		
		assert gold or test
		
		eventType = k[0] #'EventType'
		if gold and test:
			scores[eventType]['TP'] = scores[eventType]['TP'] + 1
		elif gold:
			scores[eventType]['FN'] = scores[eventType]['FN'] + 1
		elif test:
			scores[eventType]['FP'] = scores[eventType]['FP'] + 1
		
	return scores
	
def combineCounters(c1,c2):
	newScores = defaultdict(Counter)
	combinedKeys1 = list(set(c1.keys() + c2.keys()))
	for k1 in combinedKeys1:
		combinedKeys2 = list(set(c1[k1].keys() + c2[k1].keys()))
		for k2 in combinedKeys2:
			newScores[k1][k2] = c1[k1][k2] + c2[k1][k2]
	return newScores
	
def compare(goldTxtFile,goldA1File,goldA2File,testTxtFile,testA1File,testA2File):
	gText,gDenotations,gRelations,gModifications = loadDataFromSTFormat(goldTxtFile,goldA1File,goldA2File)
	tText,tDenotations,tRelations,tModifications = loadDataFromSTFormat(testTxtFile,testA1File,testA2File)
	
	# TODO: Check modifications (and others if needed)
	# TODO: Allow more than two-way triggerless relation evaluation
	
	# First gather gold relations and build events (or separate into triggerless stuff
	gEvents,gTriggerless = groupEventsAndRelations(gDenotations,gRelations)
	tEvents,tTriggerless = groupEventsAndRelations(tDenotations,tRelations)
	
	gMods = groupModifications(gDenotations,gModifications)
	tMods = groupModifications(tDenotations,tModifications)
	
	eventScores = compareEvents(gEvents,tEvents)
	relationScores = compareRelations(gTriggerless,tTriggerless)
	modScores = compareModifications(gMods,tMods)
	
	return combineCounters(combineCounters(eventScores,relationScores),modScores)

if __name__ == "__main__":
	argparser = argparse.ArgumentParser(description='Evaluation tool for event/relation extraction results')
	argparser.add_argument('--goldDir', required=True, type=str, help='Directory containing gold files')
	argparser.add_argument('--goldFormat', default="ST", type=str, help='Format to load files (ST/JSON, default=ST)')
	argparser.add_argument('--testDir', required=True, type=str, help='Directory containing test files')
	argparser.add_argument('--testFormat', default="ST", type=str, help='Format to load files (ST/JSON, default=ST)')
	args = argparser.parse_args()
	
	goldDir = args.goldDir
	if goldDir[-1] != '/':
		goldDir = goldDir + '/'
		
	testDir = args.testDir
	if testDir[-1] != '/':
		testDir = testDir + '/'
	
	allScores = defaultdict(Counter)
	for filename in os.listdir(goldDir):
		if args.goldFormat == "ST" and filename.endswith(".txt"):			
			filenameNoExt = filename[:-4]
			#prefix = inDir + filenameNoExt
			goldTxtFile = goldDir + filenameNoExt + '.txt'
			goldA1File = goldDir + filenameNoExt + '.a1'
			goldA2File = goldDir + filenameNoExt + '.a2'
			
			testTxtFile = testDir + filenameNoExt + '.txt'
			testA1File = testDir + filenameNoExt + '.a1'
			testA2File = testDir + filenameNoExt + '.a2'

			assert os.path.exists(goldA2File), "Cannot find gold file: %s" % goldA2File
			assert os.path.exists(testA2File), "Cannot find test file: %s" % testA2File
			
			#theseScores = compare(goldTxtFile,goldA1File,goldA2File, testTxtFile,testA1File,testA2File)
			theseScores = compare(goldTxtFile,goldA1File,goldA2File, goldTxtFile,goldA1File,testA2File)
			
			allScores = combineCounters(allScores, theseScores)
			#gText,gDenotations,gRelations,gModifications,gCoreferences,gEquivalences = loadDataFromSTFormat(goldTxtFile,goldA1File,goldA2File)
			#tText,tDenotations,tRelations,tModifications,tCoreferences,tEquivalences = loadDataFromSTFormat(testTxtFile,testA1File,testA2File)
			
			
#		elif args.goldFormat == "JSON" and filename.endswith(".json"):
#			jsonFile = inDir + filename
#			allSentenceAndEventData[filenameNoExt] = (sentenceData,events,modifiers,coreferences,equivalences)
	
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

		
	recall,precision,f1score,f0point1score = 0.0,0.0,0.0,0.0
	if tp > 0:
		recall = tp / float(tp+fn)
		precision = tp / float(tp + fp)
		f1score = 2*(precision*recall)/(precision+recall)
		beta = 0.1
		f0point1score = (1+beta*beta)*(precision*recall)/(beta*beta*precision+recall)

	print
	print "Summary\tR=%.3f\tP=%.3f\tF1=%.3f\tF0.1=%.3f" % (recall,precision,f1score,f0point1score)

