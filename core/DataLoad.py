import codecs
import os
import json
from pprint import pprint
import sys
import re

def loadTrigger(line,text):
	assert line[0] == 'T', "Trigger input should start with a T"
	split = line.strip().split('\t')
	assert len(split) == 3
	id = split[0]
	typeInfo = split[1]
	tokens = split[2]
		
	textChunks = []
	typeSpacePos = typeInfo.index(' ')
	typeName = typeInfo[:typeSpacePos]
	positionText = typeInfo[typeSpacePos:]
	positions = []
	for coordinates in positionText.strip().split(';'):
		a,b = coordinates.strip().split(' ')
		a,b = int(a.strip()),int(b.strip())
		textChunk = text[a:b].replace('\n',' ').strip()
		textChunks.append(textChunk)
		positions.append((a,b))
		
	# Check that the tokens match up to the text
	chunkTest = " ".join(textChunks)
	tokensTest = tokens
	chunkTest = re.sub(r'\s\s+', ' ', chunkTest)
	tokensTest = re.sub(r'\s\s+', ' ', tokensTest)
	chunkTest = chunkTest.strip()
	tokensTest = tokensTest.strip()

	#print chunkTest, '|', tokensTest
	assert chunkTest == tokensTest , u"For id=" + id + ", tokens '" + tokens.encode('ascii', 'ignore') + "' don't match up with positions: " + str(positions)
	
	trigger = (typeName, positions, tokens)
	return id,trigger
	
def loadEvent(line):
	assert line[0] == 'E', "Event input should start with a E"
	split = line.strip().split('\t')
	id = split[0]
	eventInfo = split[1]
	typeSpacePos = eventInfo.index(' ')
	
	arguments = {}
	eventNameSplit = eventInfo[:typeSpacePos].split(':')
	assert len(eventNameSplit) <= 2
	eventName = eventNameSplit[0]
	if len(eventNameSplit) == 2:
		eventTrigger = eventNameSplit[1]
	else:
		eventTrigger = None
		
	argumentText = eventInfo[typeSpacePos:]
	for argument in argumentText.strip().split(' '):
		split2 = argument.strip().split(':')
		assert len(split2) == 2
		argName = split2[0]
		triggerID = split2[1]
		assert not argName in arguments
		arguments[argName] = triggerID
	event = (eventName, eventTrigger, arguments)
	return id,event
	
def loadModifier(line):
	assert line[0] == 'M', "Modifier input should start with a M"
	split = line.strip().split('\t')
	id = split[0]
	modifierInfo = split[1].strip().split(' ')
	assert len(modifierInfo) == 2, 'Only expecting the type and subject in the modifier'
	type = modifierInfo[0]
	subject = modifierInfo[1]
	return (type, subject)
	
def loadDataFromSTFormat(txtFile,a1File,a2File):
	with codecs.open(txtFile, "r", "utf-8") as f:
		text = f.read()
			
	triggers = {}
	with codecs.open(a1File, "r", "utf-8") as f:
		for line in f:			
			assert line[0] == 'T', "Only triggers are expected in a1 file: " + a1File
			id,trigger = loadTrigger(line.strip(), text)
			triggers[id] = trigger
			
	events = {}
	predictedTriggers = {}
	modifications = {}
	if os.path.exists(a2File):
		with codecs.open(a2File, "r", "utf-8") as f:
			for line in f:
				if line[0] == 'E':
					id,event = loadEvent(line)
					events[id] = event
				elif line[0] == 'T':
					id,trigger = loadTrigger(line.strip(), text)
					predictedTriggers[id] = trigger
				elif line[0] == 'M':
					id,modifier = loadModifier(line.strip())
					modifications[id] = modifier
				elif line[0] == '*':
					print "Skipping '*' equivalences"
				else:
					raise RuntimeError('Unknown data type to be loaded in file: ' + a2File)
	else:
		print "Note: No A2 file found. ", a2File

	denotations = triggers
	relations = []
	for eventid,event in events.iteritems():
		eventName,eventTrigger,arguments = event
		if eventTrigger is None:
			assert len(arguments) == 2, "Trigger-less events must have exactly two arguments"
			argKeys = sorted(arguments.keys())
			id1 = arguments[argKeys[0]]
			id2 = arguments[argKeys[1]]
			relName = (eventName,argKeys[0],argKeys[1]) # False for triggerless
			relation = (relName, id1, id2)
			relations.append(relation)
		else:
			denotations[eventid] = predictedTriggers[eventTrigger]
			for argName,denotationID in arguments.iteritems():
				#relName = (True, eventName, argName) # True for triggered
				relation = (argName, eventid, denotationID)
				if denotationID in predictedTriggers:
					assert denotationID[0] == 'E'
					denotations[denotationID] = predictedTriggers[denotationID]
				relations.append(relation)
		
			
	return text,denotations,relations,modifications
	
def loadDataFromJSON(filename):
	denotations = {}
	relations = []
	modifications = {}
	
	with open(filename) as f:
		data = json.load(f)
		text = data['text']
		if 'denotations' in data:
			for d in data['denotations']:
				id = d['id']
				type = d['obj']
				span = d['span']
				start,end = span['begin'],span['end']
				denotation = (type,[(start,end)],None)
				denotations[id] = denotation
		if 'relations' in data:
			for r in data['relations']:
				id = r['id']
				obj = r['obj']
				pred = r['pred']
				subj = r['subj']
				relation = (pred,obj,subj)
				relations.append(relation)
		if 'modifications' in data:
			for m in data['modifications']:
				id = m['id']
				obj = m['obj']
				pred = m['pred']
				modification = (pred,obj)
				modifications[id] = modification

		expected = ['denotations','divid','modifications','namespaces','project','relations','sourcedb','sourceid','target','text']
		extraFields = [ k for k in data.keys() if not k in expected]
		assert len(extraFields) == 0, "Found additional unexpected fields (%s) in JSON FILE : %s" % (",".join(extraFields), filename)

	return text,denotations,relations,modifications

