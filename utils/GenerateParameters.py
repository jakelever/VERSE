import sys
import random
import argparse

def randomizeParameter_bool(parameters, parametername):
	if random.random() < 0.95 and parametername in parameters:
		p = bool(parameters[parametername])
	else:
		p = random.choice([True,False])
	return p
	
def randomizeParameter_int(parameters, parametername, min, max, deviation):
	if random.random() < 0.95 and parametername in parameters:
		p = int(parameters[parametername])
		if random.random() < 0.05:
			p = p + random.randint(-deviation,deviation)
	else:
		p = random.randint(min,max)
	return p
	
def randomizeParameter_float(parameters, parametername, min, max, deviation):
	if random.random() < 0.95 and parametername in parameters:
		p = float(parameters[parametername])
		if random.random() < 0.05:
			p = p + (2*deviation*random.random() - deviation)
	else:
		p = (max-min)*random.random() + min
	return p
	
def randomizeParameter_choice(parameters, parametername, choices):
	if random.random() < 0.95 and parametername in parameters:
		p = parameters[parametername]
	else:
		p = random.choice(choices)
	return p
	
def randomizeParameter_sample(parameters, parametername, choices, startMin, startMax):
	if random.random() < 0.95 and parametername in parameters:
		sample = parameters[parametername].split(",")
		if random.random() < 0.05:
			missing = [ c for c in choices if c not in sample]
			if len(missing) > 0 and random.random() < 0.5:
				sample.append(random.choice(missing))
			else:
				sample.remove(random.choice(sample))
	else:
		sample = random.sample(choices,random.randint(startMin,min(startMax,len(choices))))
	
	p = ",".join(sorted(sample))
	return p

if __name__ == "__main__":

	argparser = argparse.ArgumentParser(description='Generate parameter set for VERSE (either completely new, or tweaking existing set)')
	argparser.add_argument('--parameters', type=str, help='Optional previous parameter set to tweak')
	args = argparser.parse_args()

	adjustExistingParameters = args.parameters and random.random() < 0.9
	#adjustExistingParameters = args.parameters

	parameters = {}
	if adjustExistingParameters:
		parameters = {}
		for arg in args.parameters.split(';'):
			name,value = arg.strip().split(":")
			parameters[name.strip()] = value.strip()
			
	#parameters['sentenceRange'] = randomizeParameter_int(parameters,'sentenceRange',0,2,1)
	parameters['sentenceRange'] = 0

	#possibleFeatures = ["ngrams","selectedngrams","bigrams","ngramsPOS","selectedngramsPOS","bigramsOfDependencyPath","typesNearSelectedTokens1","typesNearSelectedTokens2","typesNearSelectedTokens3","typesNearSelectedTokens4","typesNearSelectedTokensDep1","typesNearSelectedTokensDep2","selectedTokenTypes"]
	#possibleFeatures = ["ngrams","selectedngrams","bigrams","ngramsPOS","selectedngramsPOS","bigramsOfDependencyPath","selectedTokenTypes"]
	possibleFeatures = ["splitAcrossSentences","ngrams","selectedngrams","bigrams","ngramsPOS","selectedngramsPOS","ngramsOfDependencyPath","bigramsOfDependencyPath","selectedTokenTypes","lemmas","selectedlemmas","dependencyPathElements","dependencyPathNearSelected","skipgrams_2","skipgrams_3","skipgrams_4","skipgrams_5","skipgrams_6","skipgrams_7","skipgrams_8","skipgrams_9","skipgrams_10","ngrams_betweenEntities","bigrams_betweenEntities"]
	
	for i in range(1,10):
		possibleFeatures.append("ngrams_entityWindowLeft_%d" % i)
		possibleFeatures.append("ngrams_entityWindowRight_%d" % i)
		possibleFeatures.append("ngrams_entityWindowBoth_%d" % i)
		possibleFeatures.append("bigrams_entityWindowBoth_%d" % i)
		
	for i in range(2,10):
		possibleFeatures.append("bigrams_entityWindowLeft_%d" % i)
		possibleFeatures.append("bigrams_entityWindowRight_%d" % i)
	
	if parameters['sentenceRange'] == 0 and "splitAcrossSentences" in possibleFeatures:
		possibleFeatures.remove("splitAcrossSentences")

	parameters['featureChoice'] = randomizeParameter_sample(parameters, 'featureChoice', possibleFeatures, 5,20)
		
	parameters['classifier'] = randomizeParameter_choice(parameters, 'classifier', ['SVM','LogisticRegression'])
	#parameters['classifier'] = 'SVM'

	parameters['doFeatureSelection'] = randomizeParameter_bool(parameters,'doFeatureSelection')
	if parameters['doFeatureSelection']:
		parameters['featureSelectPerc'] = randomizeParameter_int(parameters,'featureSelectPerc',1,50,2)

	parameters['svmAutoClassWeights'] = randomizeParameter_bool(parameters,'svmAutoClassWeights')
	if not parameters['svmAutoClassWeights']:
		parameters['svmClassWeight'] = randomizeParameter_int(parameters,'featureSelectPerc',1,100,5)

	#parameters['kernel'] = randomizeParameter_choice(parameters,'kernel',["linear","poly","rbf","sigmoid"])
	parameters['kernel'] = 'linear'
	


	parameters['tfidf'] = randomizeParameter_bool(parameters,'tfidf')

	parameters['threshold'] = randomizeParameter_float(parameters,'C',0.0,1.0,0.05)

	svmParameters = ['C','degree','gamma','coef0','shrinking']
	logisticRegressionParameters = ['threshold']
	if parameters['classifier'] == 'SVM':
		if random.random() < 0.1:
			parameters['C'] = randomizeParameter_float(parameters,'C',0.0,1.0,0.05)
		if random.random() < 0.1 and parameters['kernel'] == 'poly':
			parameters['degree'] = randomizeParameter_int(parameters,'degree',1,6,1)
		if random.random() < 0.1 and parameters['kernel'] in ['rbf','poly','sigmoid']:
			parameters['gamma'] = randomizeParameter_float(parameters,'gamma',0.0,1.0,0.05)
		if random.random() < 0.1 and parameters['kernel'] in ['poly','sigmoid']:
			parameters['coef0'] = randomizeParameter_float(parameters,'coef0',0.0,1.0,0.05)
		if random.random() < 0.1:
			parameters['shrinking'] = randomizeParameter_bool(parameters,'shrinking')

		if 'degree' in parameters and not parameters['kernel'] == 'poly':
			del parameters['degree']
		if 'gamma' in parameters and not parameters['kernel'] in ['rbf','poly','sigmoid']:
			del parameters['gamma']
		if 'coef0' in parameters and not parameters['kernel'] in ['poly','sigmoid']:
			del parameters['coef0']

		parameters = { k:v for k,v in parameters.iteritems() if not k in logisticRegressionParameters }
	elif parameters['classifier'] == 'LogisticRegression':
		parameters['threshold'] = randomizeParameter_float(parameters,'threshold',0.0,1.0,0.05)
		parameters = { k:v for k,v in parameters.iteritems() if not k in svmParameters }
	
	if 'featureSelectPerc' in parameters and not parameters['doFeatureSelection']:
		del parameters['featureSelectPerc']
		
	sortedKeys = sorted(parameters.keys())
	parameterTxt = " ; ".join([ "%s:%s" % (k,str(parameters[k])) for k in sortedKeys ])
	print parameterTxt
