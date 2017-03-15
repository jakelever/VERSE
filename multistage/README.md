# Plan for Multi-stage classification

The plan is to adapt VERSE into a two-stage process in which a triage classifier selects from a set of classifiers to use for each candidate relations.

This idea is inspired by the LitWay approach of two classifiers (one RegEx based and one SVM? based).

Steps for method
- The buildModel script creates a large matrix of features by samples. We should try some unsupervised clustering on that.
- Let's say we do some clustering (perhaps not K-means due to high dimensionality). Pick 3 clusters and then train classifiers for each of those separately
- Then the useModel script needs to assign a new candidate to the cluster and then use the corresponding classifier
