
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

	parser.add_argument('--inPickle', required=True, type=str, help='')
	parser.add_argument('--outPickle', required=True, type=str, help='')

	args = parser.parse_args()

	with open(args.inPickle, 'r') as f:
		data = pickle.load(f)
	print "Loaded " + args.inPickle
	
	print "Blanking predicted data..."
	for filename in data:
		(sentenceData,_,_) = data[filename]
		for s in sentenceData:
			s.eventTriggerLocs = {}
			s.eventTriggerTypes = {}
			s.refreshTakenLocs()
			s.invertTriggers()
		relations = []
		modifications = {}
		data[filename] = (sentenceData,relations,modifications)

			
	with open(args.outPickle, 'w') as f:
		pickle.dump(data,f)
		
	print "Complete."
