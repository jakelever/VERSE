import json
import sys

filename = sys.argv[1]

with open(filename) as f:
	data = json.load(f)

newData = {}
for x in ['text','sourcedb','sourceid']:
	newData[x] = data[x]

entityRenames = ['Protein_domain','DNA']

if 'denotations' in data:
	newData['denotations'] = []
	for d in data['denotations']:
		assert sorted(d.keys()) == [u'id', u'obj', u'span']
		assert sorted(d['span'].keys()) == [u'begin',u'end']

		if d['obj'] in entityRenames:
			d['obj'] = 'Entity'
			
		newData['denotations'].append(d)

if 'relations' in data:
	newData['relations'] = data['relations']

if 'modifications' in data:
	newData['modifications'] = data['modifications']

with open(filename,'w') as f:
	json.dump(newData, f)

print "Completed %s" % filename
