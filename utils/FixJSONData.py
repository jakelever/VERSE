import json
import sys

#inFilename = sys.argv[1]
#outFilename = sys.argv[2]
filename = sys.argv[1]

predictedTypes = set(['Protein'])

with open(filename) as f:
	data = json.load(f)

newData = {}

for x in ['text','sourcedb','sourceid']:
	newData[x] = data[x]

newID = 1

entityRenames = ['Protein_domain','DNA']

idConversions = {}
if 'denotations' in data:
	newData['denotations'] = []
	for d in data['denotations']:
		#print r
		assert sorted(d.keys()) == [u'id', u'obj', u'span']
		assert sorted(d['span'].keys()) == [u'begin',u'end']

		if d['obj'] in entityRenames:
			d['obj'] = 'Entity'
			
		if not d['obj'] in predictedTypes and d['id'][0] == 'T':
			newIDTxt = "EE%d" % newID
			idConversions[d['id']] = newIDTxt
			d['id'] = newIDTxt
			newID += 1
		
			
		newData['denotations'].append(d)

if 'relations' in data:
	newData['relations'] = []
	for r in data['relations']:
		#print r
		assert sorted(r.keys()) == [u'id', u'obj', u'pred', u'subj']

		if r['obj'] in idConversions:
			r['obj'] = idConversions[r['obj']]
		if r['subj'] in idConversions:
			r['subj'] = idConversions[r['subj']]
		newData['relations'].append(r)

if 'modifications' in data:
	newData['modifications'] = []
	for m in data['modifications']:
		assert sorted(m.keys()) == [u'id', u'obj', u'pred']
		if m['obj'] in idConversions:
			m['obj'] = idConversions[m['obj']]
		newData['modifications'].append(m)

with open(filename,'w') as f:
	json.dump(newData, f)

print "Completed %s" % filename
