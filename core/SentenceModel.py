
# This attempts to import networkx which is used by the ML code to look at the dependency path of a sentence
# It isn't used by the parser so Jython doesn't necessarily need it
try:
    import networkx as nx
except ImportError:
    print "Failed to import networkx, but ignored"

import itertools
from collections import defaultdict

class Token:
	def __init__(self,word,lemma,partofspeech,startPos,endPos):
		self.word = word
		self.lemma = lemma
		self.partofspeech = partofspeech
		self.startPos = startPos
		self.endPos = endPos

class SentenceModel:
	def printDependencyGraph(self):
		print "digraph sentence {"
		used = set()
		for a,b,_ in self.dependencies:
			used.update([a,b])
			aTxt = "ROOT" if a == -1 else str(a)
			bTxt = "ROOT" if b == -1 else str(b)

			print "%s -> %s;" % (aTxt,bTxt)

		for i,token in enumerate(self.tokens):
			if i in used:
				print "%d [label=\"%s\"];" % (i,token.word)
		print "}"
		
	def __str__(self):
		tokenWords = [ t.word for t in self.tokens ]
		return " ".join(tokenWords)

	def getEdgeTypes(self,edges):
		types = [ t for a,b,t in self.dependencies if (a,b) in edges or (b,a) in edges ]
		return types

	def extractSubgraphToRoot(self,minSet):
		neighbours = defaultdict(list)
		for a,b,_ in self.dependencies:
			neighbours[b].append(a)
			
		toProcess = list(minSet)
		alreadyProcessed = []
		edges = []
		while len(toProcess) > 0:
			thisOne = toProcess[0]
			toProcess = toProcess[1:]
			alreadyProcessed.append(thisOne)
			for a in neighbours[thisOne]:
				if not a in alreadyProcessed:
					toProcess.append(a)
					edges.append((a,thisOne))
		return alreadyProcessed,edges
		
	def extractMinSubgraphContainingNodes(self, minSet):
		import networkx as nx
		
		assert isinstance(minSet, list)
		for i in minSet:
			assert isinstance(i, int)
			assert i >= 0
			assert i < len(self.tokens)
		G1 = nx.Graph()
		for a,b,_ in self.dependencies:
			G1.add_edge(a,b)

		G2 = nx.Graph()
		paths = {}

		#print "-"*30
		#print [ (i,t) for i,t in enumerate(self.tokens) ]
		#print
		#print self.dependencies
		#print
		#print self.eventTriggerLocs
		#print self.argumentTriggerLocs
		#print
		#print minSet
		#self.printDependencyGraph()
		#print "-"*30

		minSet = sorted(list(set(minSet)))
		setCount1 = len(minSet)
		minSet = [ a for a in minSet if G1.has_node(a) ]
		setCount2 = len(minSet)
		if setCount1 != setCount2:
			print "WARNING. %d node(s) not found in dependency graph!" % (setCount1-setCount2)
		for a,b in itertools.combinations(minSet,2):
			try:
				path = nx.shortest_path(G1,a,b)
				paths[(a,b)] = path
				G2.add_edge(a,b,weight=len(path))
			except nx.exception.NetworkXNoPath:
				print "WARNING. No path found between nodes %d and %d!" % (a,b)
			
		# TODO: This may through an error if G2 ends up having multiple components. Catch it gracefully.
		minTree = nx.minimum_spanning_tree(G2)
		nodes = set()
		allEdges = set()
		for a,b in minTree.edges():
			path = paths[(min(a,b),max(a,b))]
			for i in range(len(path)-1):
				a,b = path[i],path[i+1]
				edge = (min(a,b),max(a,b))
				allEdges.add(edge)
			nodes.update(path)

		return nodes,allEdges
	

	def buildDependencyInfo(self):
		self.dep_neighbours = defaultdict(set)
		for (a,b,type) in self.dependencies:
			self.dep_neighbours[a].add(b)
			self.dep_neighbours[b].add(a)
		self.dep_neighbours2 = defaultdict(set)
		for i in self.dep_neighbours:
			for j in self.dep_neighbours[i]:
				self.dep_neighbours2[i].update(self.dep_neighbours[j])
			self.dep_neighbours2[i].discard(i)
			for j in self.dep_neighbours[i]:
				self.dep_neighbours2[i].discard(j)

	def addEventTrigger(self,triggerid,locs,type):
		#for loc in locs:
		#	assert not loc in self.takenLocs, 'Triggers cannot overlap'
		#	self.takenLocs.add(loc)
		assert not tuple(locs) in self.takenLocs, 'Triggers cannot overlap exactly'
			
		assert not triggerid in self.eventTriggerLocs, "Trigger ID already exists in sentence"
		assert not triggerid in self.argumentTriggerLocs, "Trigger ID already exists in sentence"
					
		self.eventTriggerLocs[triggerid] = locs
		self.eventTriggerTypes[triggerid] = type
		#self.locsToTriggerIDs[locs] = triggerid
		
	def invertTriggers(self):
		self.locsToTriggerIDs = {}
		self.locsToTriggerTypes = {}
		for triggerid,locs in self.eventTriggerLocs.iteritems():
			type = self.eventTriggerTypes[triggerid]
			self.locsToTriggerIDs[tuple(locs)] = triggerid
			self.locsToTriggerTypes[tuple(locs)] = type
		for triggerid,locs in self.argumentTriggerLocs.iteritems():
			type = self.argumentTriggerTypes[triggerid]
			self.locsToTriggerIDs[tuple(locs)] = triggerid
			self.locsToTriggerTypes[tuple(locs)] = type
		#print "MOO"

	def refreshTakenLocs(self):
		self.takenLocs = set()
		for triggerid,locs in self.eventTriggerLocs.iteritems():
			for loc in locs:
				assert loc >= 0
				assert loc < len(self.tokens)
				assert not loc in self.takenLocs, 'Triggers cannot overlap'
				#self.takenLocs.add(loc)
			self.takenLocs.add(tuple(locs))
		for triggerid,locs in self.argumentTriggerLocs.iteritems():
			for loc in locs:
				assert loc >= 0
				assert loc < len(self.tokens)
				assert not loc in self.takenLocs, 'Triggers cannot overlap'
				#self.takenLocs.add(loc)
			self.takenLocs.add(tuple(locs))

	def __init__(self, tokens, dependencies, eventTriggerLocs, eventTriggerTypes, argumentTriggerLocs, argumentTriggerTypes):
		assert isinstance(tokens, list) 
		assert isinstance(dependencies, list) 
		assert isinstance(eventTriggerLocs, dict) 
		assert isinstance(eventTriggerTypes, dict)
		assert isinstance(argumentTriggerLocs, dict) 
		assert isinstance(argumentTriggerTypes, dict)
		
		assert len(eventTriggerLocs) == len(eventTriggerTypes)
		assert len(argumentTriggerLocs) == len(argumentTriggerTypes)
		
		self.tokens = tokens
		self.eventTriggerLocs = eventTriggerLocs
		self.eventTriggerTypes = eventTriggerTypes
		self.argumentTriggerLocs = argumentTriggerLocs
		self.argumentTriggerTypes = argumentTriggerTypes
		self.dependencies = dependencies
	
		self.refreshTakenLocs()
		self.invertTriggers()

