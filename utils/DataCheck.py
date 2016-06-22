import sys
from collections import OrderedDict

descriptionFile = sys.argv[1]
a1File = sys.argv[2]
a2File = sys.argv[3]
a2Out = sys.argv[4]



allNames = set()
triggers = OrderedDict()
with open(a1File) as f:
	for line in f:
		line = line.strip()
		if line[0] == 'T':
			id,stuff,tokens = line.split('\t')
			split = stuff.split(' ')
			name = split[0]
			triggers[id] = name
			allNames.add(name)

acceptable = {}
with open(descriptionFile) as f:
	for line in f:
		split = line.strip().split('\t')
		assert len(split) == 3
		info = split[0].split(';')
		assert len(info) == 3
		name = info[0]
		argNames = info[1:]
		key = tuple(info)

		if split[1] == '*':
			arg1Types = list(allNames)
		else:
			arg1Types = split[1].split('|')
		if split[2] == '*':
			arg2Types = list(allNames)
		else:
			arg2Types = split[2].split('|')

		acceptableArgs = (arg1Types,arg2Types)
		acceptable[key] = acceptableArgs

events = OrderedDict()
eventOriginalText = OrderedDict()
with open(a2File) as f:
	for line in f:
		line = line.strip()
		if line[0] == 'E':
			id,stuff = line.split('\t')
			split = stuff.split(' ')
			name = split[0]
			args = split[1:]
			args = [ tuple(arg.split(':')) for arg in args ]
			args = sorted(args)
			event = (name,args)
			events[id] = event
			eventOriginalText[id] = line


#print events
okayCount = 0
with open(a2Out,'w') as f:
	for id,(name,args) in events.iteritems():
		#print args
		#argTxt = [ "%s:%s" % (a,triggers[b]) for a,b in args ]
		#print "%s %s" % (name," ".join(argTxt))

		argNames = [ a for a,b in args ]
		argTypes = [ triggers[b] for a,b in args ]

		key = tuple([name] + argNames)
		if not key in acceptable:
			print "Event has unrecognised arguments:", id, key
			continue

		acceptableTypes = acceptable[key]

		failed = False
		for argName,argType,acceptableType in zip(argNames,argTypes,acceptableTypes):
			if not argType in acceptableType:
				print "Event has incorrect type:", id, name, argName, argType
				failed = True

		if failed:
			continue
		
		okayCount += 1
		originalText = eventOriginalText[id]
		f.write(originalText + "\n")
	#print "%s;%s\t%s" % (name,";".join(argNames),"\t".join(argTypes))

print "%d of %d events written to %s" % (okayCount,len(events),a2Out)
