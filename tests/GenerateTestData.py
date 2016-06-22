#-*- coding: utf-8 -*-

import sys
import argparse
from collections import defaultdict
import string
import random

if __name__ == "__main__":

	random.seed(1)

	# Set up the command line arguments
	parser = argparse.ArgumentParser(description='Generate a set of test data')
	#parser.add_argument('--selectedTypeIDs', required=True, type=str, help='Comma-delimited list of type IDs that should be included in the word-list')
	#parser.add_argument('--selectedRelTypes', type=str, help='Comma-delimited list of relationship types that should be included in the word-list (e.g. has_tradename)')
	
	#parser.add_argument('--umlsConceptFile', required=True, type=argparse.FileType('r'), help='The concept file from the UMLS dataset')
	#parser.add_argument('--umlsSemanticTypesFile', required=True, type=argparse.FileType('r'), help='The semantic types file from the UMLS dataset')
	
	parser.add_argument('--outTxtFile', required=True, type=argparse.FileType('w'), help='')
	parser.add_argument('--outA1File', required=True, type=argparse.FileType('w'), help='')
	parser.add_argument('--outA2File', required=True, type=argparse.FileType('w'), help='')
	parser.add_argument('--exampleCount', required=True, type=int, help='')
	parser.add_argument('--testType', required=True, type=str, help='')
	parser.add_argument('--triggerless', action='store_true')
	args = parser.parse_args()
	
	# options = ["ngrams","selectedngrams","bigrams","ngramsPOS","selectedngramsPOS","bigramsOfDependencyPath","typesNearSelectedTokens1","typesNearSelectedTokens2","typesNearSelectedTokens3","typesNearSelectedTokens4","typesNearSelectedTokensDep1","typesNearSelectedTokensDep2"]
	
	#type = 'trigger'
	
	nouns = {}
	adjectives = {}
	propernouns = {}
	
	eventTypes = ['None','Gene_expression','Positive_regulation']
	
	# 'home','television','telephone','picture','desk','hope','rover','screen','paper','plant','clock']
	nouns[0] = ['horse','cow','sheep','pig','goat','llama']
	adjectives[0] = ['small','big','difficult','tiny','massive','huge','large','gigantic']
	propernouns[0] = ['Chloë','Alan','Chris','Sally','Dave','Eric','Sarah'] #'Volvo','Renault','Washington']
	
	nouns[1] = ['jalapeño','éclair','pizza','pie','cake','icecream','cocktail','beer']
	adjectives[1] = ['blue','green','yellow','pink','black','red','turquoise','orange']
	propernouns[1] = ['Zaïre','London','Sydney','Glasgow','Edinburgh','Ottawa','Vancouver','Calgary','Denver','Lima']
	
	nouns[2] = ['plane','helicopter','handglider','skydiver','zeppelin','blimp','jet']
	adjectives[2] = ['naïve','old','ancient','young','childish','teenage']
	propernouns[2] = ['America','Canada','Kenya','Scotland','Tunisia','Ethiopia','Korea']
	
	#for i in range(len(eventTypes)):
	#	nouns[i] = nouns[i][:2]
	#	adjectives[i] = adjectives[i][:2]
	#	propernouns[i] = propernouns[i][:2]
	
	allNouns = sum(nouns.values(),[])
	allAdjectives = sum(adjectives.values(),[])
	allPropernouns = sum(propernouns.values(),[])
	
	# The dysregulation of XYZ3 is a bad thing.
	formats = ['The @NOUN of 1PROPERNOUN is $ADJECTIVE']
				#'While discussing &PROPERNOUN and &PROPERNOUN, one should be away that $ADJECTIVE @NOUN is associated with 1PROPERNOUN.']
				#'The one $ADJECTIVE+$NOUN that belonged to $PROPERNOUN could be described as $ADJECTIVE',
				#'The $ADJECTIVE+$NOUN was last seen going to $PROPERNOUN',
				#'Everyone says that the $ADJECTIVE+$NOUN in $PROPERNOUN is $ADJECTIVE',
				#'They purchased the $ADJECTIVE+$NOUN and $ADJECTIVE+$NOUN in $PROPERNOUN']
	
#	exampleCount = 100
	
	tmpEventID = 1
	tmpTriggerID = 1
	currentLoc = 0
	allTxt = ""
	for i in range(args.exampleCount):
		chosenEventType = random.randint(0,len(eventTypes)-1)
		
		if args.testType == 'selectedngrams':
			nounChoice = nouns[chosenEventType]
			adjChoice = allAdjectives
			propernounChoice = propernouns[chosenEventType]
		elif args.testType == 'ngrams':
			nounChoice = allNouns
			adjChoice = adjectives[chosenEventType]
			propernounChoice = allPropernouns
		else:
			raise RuntimeError('Unknown --testType: %s' % args.testType)
		
		sentence = random.choice(formats).split(' ')
		newSentence = []
		event = {}
		locs = []
		for i in range(len(sentence)):
			w = sentence[i]
			if w[:1] == '@':
				event['trigger'] = i
			elif w[:1] == '1':
				event['arg1'] = i
			elif w[:1] == '2':
				event['arg1'] = i
			elif w[:1] == '3':
				event['arg1'] = i
			
			if w[1:] == 'NOUN':
				newWs = [random.choice(nounChoice)]
			elif w[1:] == 'ADJECTIVE':
				newWs = [random.choice(adjChoice)]
			elif w[1:] == 'ADJECTIVE+NOUN':
				newWs = [random.choice(adjChoice),random.choice(nounChoice)]
			elif w[1:] == 'PROPERNOUN':
				newWs = [random.choice(propernounChoice)]
			else:
				newWs = [w]
				
			for newW in newWs:
				wordLen = len(newW.decode('utf8'))
				loc = (currentLoc,currentLoc+wordLen)
				locs.append(loc)
				currentLoc = currentLoc + wordLen + 1
				newSentence.append(newW)
				
		#print event
			
		sentenceEnd = ". "
		sentenceTxt = " ".join(newSentence) + sentenceEnd
		currentLoc = currentLoc + len(sentenceEnd) - 1
		
		allTxt = allTxt + " " + sentenceTxt
		
		argType = "Protein"
		
		start,end = locs[event['arg1']]
		argLine = "T%d\t%s %d %d\t%s" % (tmpTriggerID, argType, start, end, newSentence[event['arg1']])

		#triggerType = "Protein"
		if chosenEventType > 0:
			triggerType = eventTypes[chosenEventType]
		else:
			triggerType = random.choice(eventTypes)

		start,end = locs[event['trigger']]
		triggerLine = "T%d\t%s %d %d\t%s" % (tmpTriggerID+1, triggerType, start, end, newSentence[event['trigger']])
		
		#print sentenceTxt
		args.outTxtFile.write(sentenceTxt)
		#print argLine
		args.outA1File.write(argLine + "\n")
		if args.triggerless:
			args.outA1File.write(triggerLine + "\n")

		if chosenEventType > 0:
			eventType = eventTypes[chosenEventType]
			
			if args.triggerless:
				eventLine = "E%d\t%s Cause:T%d Theme:T%d" % (tmpEventID, eventType, tmpTriggerID+1, tmpTriggerID)
			else:
				eventLine = "E%d\t%s:T%d Theme:T%d" % (tmpEventID, eventType, tmpTriggerID+1, tmpTriggerID)
				args.outA2File.write(triggerLine + "\n")

			args.outA2File.write(eventLine + "\n")
			
		tmpEventID = tmpEventID + 1
		tmpTriggerID = tmpTriggerID + 2
		
	
