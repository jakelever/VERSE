
import sys
import os

# Include core directory for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

import fileinput
import argparse
import time
import itertools
import pickle
import random
import codecs
from collections import defaultdict

from SentenceModel import *

# It's the main bit. Yay!
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Removes entities, relations and modifications that are to be predicted')

	parser.add_argument('--inFile', required=True, type=str, help='File to be filtered')
	parser.add_argument('--outFile', required=True, type=str, help='Filename for output filtered file')

	args = parser.parse_args()

	with open(args.inFile, 'r') as f:
		data = pickle.load(f)
	print "Loaded " + args.inFile
	
	print "Blanking predicted data..."
	for filename in data:
		(sentenceData,_,_) = data[filename]
		for s in sentenceData:
			s.predictedEntityLocs = {}
			s.predictedEntityTypes = {}
			s.refreshTakenLocs()
			s.invertTriggers()
		relations = []
		modifications = {}
		data[filename] = (sentenceData,relations,modifications)

			
	with open(args.outFile, 'w') as f:
		pickle.dump(data,f)
		
	print "Complete."
