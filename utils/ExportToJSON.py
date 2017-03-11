
import sys
import os

# Include core directory for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

import argparse
import pickle
import json

from SentenceModel import *

# It's the main bit. Yay!
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Export VERSE data to JSON format')

	parser.add_argument('--inFile', required=True, type=str, help='File to be exported')
	parser.add_argument('--origDir', required=True, type=str, help='Original directory with text data')
	parser.add_argument('--outDir', required=True, type=str, help='Output directory')
	parser.add_argument('--triggerTypes', required=True, type=str, help='Comma-delimited list of types of entities that should be event triggers')

	args = parser.parse_args()

	triggerTypes = set(args.triggerTypes.split(','))

	with open(args.inFile, 'r') as f:
		pickleData = pickle.load(f)

	outDir = args.outDir
	if outDir[-1] != '/':
		outDir += '/'

	origDir = args.origDir
	if origDir[-1] != '/':
		origDir += '/'

	#outData = {}
	for filename in pickleData:
		with open(origDir + filename + '.json') as f:
			tmpData = json.load(f)
			text = tmpData['text']
		#	sourcedb = tmpData['sourcedb']
		#	sourceid = tmpData['sourceid']

		split = filename.split('-')
		sourcedb = split[0]
		sourceid = split[1]

		outData = {'text':text,'sourcedb':sourcedb,'sourceid':sourceid,'denotations':[],'relations':[],'modifications':[]}
		idConversion = {}
		sentenceData,relations,modifications = pickleData[filename]

		topE = 0
		topT = -1
		for sentence in sentenceData:
			entityIDs = sentence.predictedEntityLocs.keys() + sentence.knownEntityLocs.keys()
			for eID in entityIDs:
				if eID[0] == 'T':
					num = int(eID[1:])
					topT = max(topT,num)

		for sentence in sentenceData:
			# {u'obj': u'Protein', u'span': {u'begin': 3871, u'end': 3874}, u'id': u'T52'}
			predictedEntities = [ (id,sentence.predictedEntityLocs[id],sentence.predictedEntityTypes[id]) for id in sentence.predictedEntityLocs ]
			knownEntities = [ (id,sentence.knownEntityLocs[id],sentence.knownEntityTypes[id]) for id in sentence.knownEntityLocs ]

			allEntities = predictedEntities + knownEntities
			for id,locs,type in allEntities:
				begin = sentence.tokens[min(locs)].startPos
				end = sentence.tokens[max(locs)].endPos
				entity = {}
				entity['obj'] = type
				entity['span'] = {'begin':begin, 'end':end}
				
				if id[:2] == 'EE':
					if type in triggerTypes:
						topE += 1
						newID = 'E%d' % topE
					else:
						topT += 1
						newID = 'T%d' % topT
					idConversion[id] = newID
					id = newID
						
				entity['id'] = id

				outData['denotations'].append(entity)

		topR = 0
		for relInfo, id1, id2, relProb in relations:
			if id1 in idConversion:
				id1 = idConversion[id1]
			if id2 in idConversion:
				id2 = idConversion[id2]

			rel = {}
			topR += 1
			rel['id'] = "R%d" % topR
			rel['obj'] = id1
			rel['pred'] = relInfo[0]
			rel['subj'] = id2
			outData['relations'].append(rel)

		topM = 0
		for modtype,entityid in modifications.values():
			if entityid in idConversion:
				entityid = idConversion[entityid]

			mod = {}
			topM += 1
			mod['id'] = "M%d" % topM
			mod['obj'] = entityid
			mod['pred'] = modtype

			outData['modifications'].append(mod)

		outFilename = outDir + filename + '.json'
		with open(outFilename,'w') as f:
			json.dump(outData,f)
		#print "Written to %s" % outFilename

