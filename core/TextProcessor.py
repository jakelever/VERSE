import sys
import fileinput
import argparse
import time
from collections import defaultdict, Counter
import itertools
import pickle
import os
import codecs
import argparse
from intervaltree import Interval, IntervalTree

from DataLoad import *
from SentenceModel import *
		
from java.util import *
from edu.stanford.nlp.pipeline import *
from edu.stanford.nlp.ling.CoreAnnotations import *
from edu.stanford.nlp.semgraph.SemanticGraphCoreAnnotations import *

pipeline = None
def getPipeline():
	global pipeline
	if pipeline is None:
		props = Properties()
		props.put("annotators", "tokenize, ssplit, pos, lemma, depparse");
		pipeline = StanfordCoreNLP(props, False)
	return pipeline
	
def within(pos,start,end):
	return pos > start and pos < end
	
from __builtin__ import zip # To deal with Jython conflict with java Zip package
def parseTextWithTriggers(text,denotations,doTokenPreprocessing,knownEntities):
	pipeline = getPipeline()

	denotationTree = IntervalTree()
	for id,(_,positions,_) in denotations.iteritems():
		for a,b in positions:
			denotationTree[a:b] = id

	if doTokenPreprocessing:
		prefixes = ["anti","phospho","translocation"]
		prefixes += [ s[0].upper()+s[1:] for s in prefixes ]
				
		suffixes = ["bound","degradable","driven","expressed","induced","induction","localized","luciferase","mediated","mediated way","nuclear","perforin","phosphorylated","Producing","promoter","promoting","secreting","silencing","simulated","transfected","translocation","costimulated","positve","regulated","responsive","independent","inducing","phosphorylation","stimulated","catalyzed","dimerization","expression","activated","reconstituted","associated","expressing","negative","producing","binding","positive","mediated","dependent","induced","deficient","protein","treatment"]
		suffixes += [ s[0].upper()+s[1:] for s in suffixes ]
		#print suffixes
		
		for prefix in prefixes:
			text = text.replace(prefix+"-",prefix+" ")
		for suffix in suffixes:
			text = text.replace("-"+suffix," "+suffix)
		
		newTokens = []
		position = 0
		for tmpToken in text.split(' '):
			startPos = position
			endPos = position + len(tmpToken)
			
			splitToken = None
			triggers = denotationTree[startPos:endPos]
			for interval in triggers:
				if within(interval.begin,startPos,endPos):
					#print word, interval, startPos, endPos, text[interval.begin:interval.end] #denotations[interval.data]
					#print "COOLA1\t%s\t%s" % (tmpToken,text[interval.begin:interval.end])
					tmpSplitToken = text[interval.begin-1]
					if tmpSplitToken in ['-','/']:
						splitToken = tmpSplitToken
						break
					#print separator
				elif within(interval.end,startPos,endPos):
					#print "COOLA2\t%s\t%s" % (tmpToken,text[interval.begin:interval.end])
					tmpSplitToken = text[interval.end]
					if tmpSplitToken in ['-','/']:
						splitToken = tmpSplitToken
						break
					#print tmpSplitToken
		
			position += len(tmpToken) + 1
			
			if splitToken is None:
				newTokens.append(tmpToken)
			else:
				newTokens += tmpToken.split(splitToken)
				
		text = u" ".join(newTokens)
	
	allSentenceData = []

	#print text
	document = pipeline.process(text)	
	for sentence in document.get(SentencesAnnotation):

		tokens = []
		triggerLocations = defaultdict(list)
		
		for i,token in enumerate(sentence.get(TokensAnnotation)):
			word = token.word()
			lemma = token.lemma()
			partofspeech = token.tag()
			startPos = token.beginPosition()
			endPos = token.endPosition()

			t = Token(word,lemma,partofspeech,startPos,endPos)
			tokens.append(t)

			triggers = denotationTree[startPos:endPos]
			for interval in triggers:
				triggerID = interval.data
				triggerLocations[triggerID].append(i)
				#if within(interval.begin,startPos,endPos) or within(interval.end,startPos,endPos):
				#if within(interval.begin,startPos,endPos):
					#print word, interval, startPos, endPos, text[interval.begin:interval.end] #denotations[interval.data]
					#print "COOL1\t%s\t%s" % (word,text[interval.begin:interval.end])
				#elif within(interval.end,startPos,endPos):
					#print "COOL2\t%s\t%s" % (word,text[interval.begin:interval.end])
					
					#print "-"*30
					#print sentence
					#sys.exit(0)

		#dparse = sentence.get(BasicDependenciesAnnotation)
		dparse = sentence.get(CollapsedCCProcessedDependenciesAnnotation)

		dependencies = []	
		
		# Get the dependency graph
		for edge in dparse.edgeIterable():
			governor = edge.getGovernor()
			governorIndex = governor.index()
			dependent = edge.getDependent()
			dependentIndex = dependent.index()
			rel = edge.getRelation().getLongName()
			dependencies.append((governorIndex-1, dependentIndex-1, rel))
			
		# Let's gather up the information about the "known" triggers in the sentence (those from the A1 file)
		eventTriggerLocs, eventTriggerTypes, argumentTriggerLocs, argumentTriggerTypes = {},{},{},{}
		for triggerID,locs in triggerLocations.iteritems():
			# Trigger is following tuple (typeName, positions, tokens)
			triggerType,_,_ = denotations[triggerID]
			if knownEntities is None or triggerType in knownEntities:
				argumentTriggerLocs[triggerID] = locs
				argumentTriggerTypes[triggerID] = triggerType
			else:
				eventTriggerLocs[triggerID] = locs
				eventTriggerTypes[triggerID] = triggerType
			
		sentenceData = SentenceModel(tokens, dependencies, eventTriggerLocs, eventTriggerTypes, argumentTriggerLocs, argumentTriggerTypes)
		allSentenceData.append(sentenceData)
	
	return allSentenceData
	
def findEventTrigger(sentenceData,triggerid):
	for sentenceid, sentence in enumerate(sentenceData):
		if triggerid in sentence.predictedEntityLocs:
			return sentenceid,sentence.predictedEntityLocs[triggerid]
	raise RuntimeError('Unable to find location of event trigger ID ('+triggerid+') in sentences')
	
def findArgumentTrigger(sentenceData):
	for sentenceid, sentence in enumerate(sentenceData):
		if triggerid in sentence.knownEntityLocs:
			return sentenceid,sentence.knownEntityLocs[triggerid]
	raise RuntimeError('Unable to find location of argument trigger ID ('+triggerid+') in sentences')

def isComplexEvent(eventTrigger,arguments):
	if eventTrigger[0] == 'E':
		return True
	for _,id in arguments.iteritems():
		if id[0] == 'E':
			return True
	return False
	
#def associatedEvents(sentenceData,events,modifiers,coreferences,equivalences):
#	nonCom
#	complexEvents = []
#	for eventid,event in events.iteritems():
#		(eventName, eventTrigger, arguments) = event
#		isComplexEvent = False
		
#		Event(eventName, 
		

# It's the main bit. Yay!
if __name__ == "__main__":

	argparser = argparse.ArgumentParser(description='Text parsing pipeline for a directory of text in ST or JSON format')
	argparser.add_argument('--inDir', required=True, type=str, help='Directory containing input files')
	argparser.add_argument('--format', default="ST", type=str, help='Format to load files (ST/JSON, default=ST)')
	argparser.add_argument('--splitTokensForGE4', action='store_true', help='Whether to split tokens using GE4 logic')
	argparser.add_argument('--knownEntities', help='Comma-separated list of entities that are known through-out')
	argparser.add_argument('--outFile', required=True, type=str, help='Output filename for parsed-text data')
	args = argparser.parse_args()
	
	assert args.format == "ST" or args.format == "JSON", "--format must be ST or JSON"

	inDir = args.inDir
	outFile = args.outFile
	print "inDir:", inDir
	print "outFile:", outFile

	if inDir[-1] != '/':
		inDir = inDir + '/'

	splitTokensForGE4 = False
	if args.splitTokensForGE4:
		splitTokensForGE4 = True
		
	knownEntities = None
	if args.knownEntities:
		knownEntities = set(args.knownEntities.split(","))
	
	allSentenceAndEventData = {}
	for filename in os.listdir(inDir):
		if args.format == "ST" and filename.endswith(".txt"):			
			filenameNoExt = filename[:-4]
			prefix = inDir + filenameNoExt
			txtFile = prefix + '.txt'
			a1File = prefix + '.a1'
			a2File = prefix + '.a2'
			
			print "### Processing %s ###" % txtFile

			assert os.path.exists(a1File), "Cannot find file: %s" % a1File
					
			text,denotations,relations,modifications = loadDataFromSTFormat(txtFile,a1File,a2File)
			
			sentenceData = parseTextWithTriggers(text,denotations,splitTokensForGE4,knownEntities)
			
			allSentenceAndEventData[filenameNoExt] = (sentenceData,relations,modifications)
		elif args.format == "JSON" and filename.endswith(".json"):
			filenameNoExt = filename[:-5]
			jsonFile = inDir + filenameNoExt + '.json'

			print "### Processing %s ###" % jsonFile

			text,denotations,relations,modifications = loadDataFromJSON(jsonFile)
			
			sentenceData = parseTextWithTriggers(text,denotations,splitTokensForGE4,knownEntities)
			
			allSentenceAndEventData[filenameNoExt] = (sentenceData,relations,modifications)

	with open(outFile, 'w') as f:
		pickle.dump(allSentenceAndEventData, f)
	print "Written to " + outFile
	
