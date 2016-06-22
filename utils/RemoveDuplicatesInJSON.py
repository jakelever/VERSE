import json
import sys

filename = sys.argv[1]

predictedTypes = set(['Protein'])

with open(filename) as f:
	data = json.load(f)

newData = {}

for x in ['text','sourcedb','sourceid']:
	newData[x] = data[x]

newID = 1

originalIDsToEntity = {}
newEntityToID = {}

#spans = set()
entities = set()
if 'denotations' in data:
	newData['denotations'] = []
	for d in data['denotations']:
		#print r
		assert sorted(d.keys()) == [u'id', u'obj', u'span']
		assert sorted(d['span'].keys()) == [u'begin',u'end']
		
		entity = (d['obj'],d['span']['begin'],d['span']['end'])
		originalIDsToEntity[d['id']] = entity
		
		if entity in entities:
			print "Found duplicate entity:", entity
		else:
			entities.add(entity)
			newEntityToID[entity] = d['id']
			newData['denotations'].append(d)

relations = set()
if 'relations' in data:
	newData['relations'] = []
	for r in data['relations']:
		#print r
		assert sorted(r.keys()) == [u'id', u'obj', u'pred', u'subj']
		
		relation = (r['pred'],originalIDsToEntity[r['obj']],originalIDsToEntity[r['subj']])

		if relation in relations:
			print "Found duplicate relation:", relation
		else:
			relations.add(relation)
			newObjID = newEntityToID[originalIDsToEntity[r['obj']]]
			newSubjID = newEntityToID[originalIDsToEntity[r['subj']]]
			
			r['obj'] = newObjID
			r['subj'] = newSubjID
		
			newData['relations'].append(r)
		

modifications = set()
if 'modifications' in data:
	newData['modifications'] = []
	for m in data['modifications']:
		assert sorted(m.keys()) == [u'id', u'obj', u'pred']
		
		modification = (r['pred'],originalIDsToEntity[r['obj']])
		
		if modification in modifications:
			print "Found duplicate modification:", relation
		else:
			modifications.add(modification)
			
			newObjID = newEntityToID[originalIDsToEntity[m['obj']]]
			m['obj'] = newObjID
			
			newData['modifications'].append(m)

with open(filename,'w') as f:
	json.dump(newData, f)

print "Completed %s" % filename
