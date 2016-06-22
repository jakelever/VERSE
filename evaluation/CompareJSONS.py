import sys
import argparse
from collections import defaultdict,Counter
import os
import json

def compareDenotations(goldData,testData):
	scores = defaultdict(Counter)
	
	gDenotations = goldData['denotations'] if 'denotations' in goldData else []
	tDenotations = testData['denotations'] if 'denotations' in testData else []
		
	goldTuples = [ (d['obj'],d['span']['begin'],d['span']['end']) for d in gDenotations ]
	testTuples = [ (d['obj'],d['span']['begin'],d['span']['end']) for d in tDenotations ]
			
	merged = set(list(goldTuples) + list(testTuples))
	
	for m in merged:
		test = m in testTuples
		gold = m in goldTuples
		
		assert test or gold
	
		eventType = m[0]
		if not test:
			scores[eventType]['FN'] = scores[eventType]['FN'] + 1
		elif not gold:
			scores[eventType]['FP'] = scores[eventType]['FP'] + 1
		else:
			scores[eventType]['TP'] = scores[eventType]['TP'] + 1
			
	return scores
	
def compareRelations(goldData,testData):
	scores = defaultdict(Counter)

	gDenotations = goldData['denotations'] if 'denotations' in goldData else []
	tDenotations = testData['denotations'] if 'denotations' in testData else []
	gRelations = goldData['relations'] if 'relations' in goldData else []
	tRelations = testData['relations'] if 'relations' in testData else []
	
	goldDenotationLookup = { d['id']:(d['span']['begin'],d['span']['end']) for d in gDenotations }
	testDenotationLookup = { d['id']:(d['span']['begin'],d['span']['end']) for d in tDenotations }
		
	goldTuples = [ (d['pred'],goldDenotationLookup[d['obj']],goldDenotationLookup[d['subj']]) for d in gRelations ]
	testTuples = [ (d['pred'],testDenotationLookup[d['obj']],testDenotationLookup[d['subj']]) for d in tRelations ]
			
	merged = set(list(goldTuples) + list(testTuples))
	
	for m in merged:
		test = m in testTuples
		gold = m in goldTuples
		
		assert test or gold
	
		eventType = m[0]
		if not test:
			scores[eventType]['FN'] = scores[eventType]['FN'] + 1
		elif not gold:
			scores[eventType]['FP'] = scores[eventType]['FP'] + 1
		else:
			scores[eventType]['TP'] = scores[eventType]['TP'] + 1
			
	return scores
	
def compareModifications(goldData,testData):
	scores = defaultdict(Counter)
	
	gDenotations = goldData['denotations'] if 'denotations' in goldData else []
	tDenotations = testData['denotations'] if 'denotations' in testData else []
	gModifications = goldData['modifications'] if 'modifications' in goldData else []
	tModifications = testData['modifications'] if 'modifications' in testData else []
	
	goldDenotationLookup = { d['id']:(d['span']['begin'],d['span']['end']) for d in gDenotations }
	testDenotationLookup = { d['id']:(d['span']['begin'],d['span']['end']) for d in tDenotations }
		
	goldTuples = [ (d['pred'],goldDenotationLookup[d['obj']]) for d in gModifications ]
	testTuples = [ (d['pred'],testDenotationLookup[d['obj']]) for d in tModifications ]
			
	merged = set(list(goldTuples) + list(testTuples))
	
	for m in merged:
		test = m in testTuples
		gold = m in goldTuples
		
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
	
def compareJSONs(goldData,testData):
	denotationScores = compareDenotations(goldData,testData)
	relationScores = compareRelations(goldData,testData)
	modificationScores = compareModifications(goldData,testData)
	return denotationScores,relationScores,modificationScores
	
def printScores(name, allScores):
	print "#"*30
	print name

	sortedEventTypes = sorted(allScores.keys())
	
	tp,fp,fn,partial = 0,0,0,0
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
		
		print "   TP=%d\tFP=%d\tFN=%d\tPartial=%d\tR=%.3f\tP=%.3f\tF1=%.3f\t%s" % (scores['TP'],scores['FP'],scores['FN'],scores['Partial'],recall,precision,f1score,eventType)
		
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
	print "%s Summary\tR=%.3f\tP=%.3f\tF1=%.3f\tF0.1=%.3f\tF10=%.3f" % (name, recall,precision,f1score,f0point1score,f10score)

if __name__ == "__main__":
	argparser = argparse.ArgumentParser(description='Evaluation tool for entity extraction results')
	argparser.add_argument('--goldDir', required=True, type=str, help='Directory containing gold files')
	argparser.add_argument('--testDir', required=True, type=str, help='Directory containing test files')
	
	argparser.add_argument('--denotationsOnly', action='store_true')
	argparser.add_argument('--relationsOnly', action='store_true')
	argparser.add_argument('--modificationsOnly', action='store_true')
	
	args = argparser.parse_args()
	
	doDenotations,doRelations,doModifications = True,True,True
	if args.denotationsOnly:
		doDenotations,doRelations,doModifications = True,False,False
	if args.relationsOnly:
		doDenotations,doRelations,doModifications = False,True,False
	if args.modificationsOnly:
		doDenotations,doRelations,doModifications = False,False,True
	
	goldDir = args.goldDir
	if not goldDir[-1] == '/':
		goldDir += '/'

	testDir = args.testDir
	if not testDir[-1] == '/':
		testDir += '/'

	allDenotationScores = defaultdict(Counter)
	allRelationScores = defaultdict(Counter)
	allModificationScores = defaultdict(Counter)
	for filename in os.listdir(goldDir):
		if filename.endswith(".json"):			
			filenameNoExt = filename[:-5]
			goldFile = goldDir + filenameNoExt + '.json'
			testFile = testDir + filenameNoExt + '.json'
			
			assert os.path.exists(goldFile), "Cannot find file: %s" % goldFile
			assert os.path.exists(testFile), "Cannot find file: %s" % testFile
			
			with open(goldFile) as f:
				goldData = json.load(f)
			with open(testFile) as f:
				testData = json.load(f)
				
			theseDenotationScores, theseRelationScores, theseModificationScores = compareJSONs(goldData,testData)
			
			allDenotationScores = combineCounters(allDenotationScores, theseDenotationScores)
			allRelationScores = combineCounters(allRelationScores, theseRelationScores)
			allModificationScores = combineCounters(allModificationScores, theseModificationScores)
			
			#break
	
	if doDenotations:
		printScores('Denotations', allDenotationScores)
	if doRelations:
		printScores('Relations', allRelationScores)
	if doModifications:
		printScores('Modifications', allModificationScores)
