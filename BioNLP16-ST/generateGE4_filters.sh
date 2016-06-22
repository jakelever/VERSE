#!/bin/bash

events="Gene_expression,Transcription,Protein_catabolism,Binding,Localization,Protein_modification,Phosphorylation,Ubiquitination,Acetylation,Deacetylation,Regulation,Positive_regulation,Negative_regulation"

for e1 in "Gene_expression" "Transcription" "Protein_catabolism" "Binding" "Localization"
do
	echo -e "themeOf\t$e1\tProtein"
	echo -e "themeOf\t$e1\tEntity"
done

for e1 in "Protein_modification" "Phosphorylation" "Ubiquitination" "Acetylation" "Deacetylation"
do
	echo -e "themeOf\t$e1\tProtein"
	echo -e "themeOf\t$e1\tEntity"
	echo -e "causeOf\t$e1\tProtein"
	echo -e "causeOf\t$e1\tEntity"
	for e2 in `echo "$events" | tr ',' '\n'`
	do
		echo -e "causeOf\t$e1\t$e2"
	done
done


for e1 in "Regulation" "Positive_regulation" "Negative_regulation"
do
	echo -e "themeOf\t$e1\tProtein"
	echo -e "themeOf\t$e1\tEntity"
	echo -e "causeOf\t$e1\tProtein"
	echo -e "causeOf\t$e1\tEntity"
	for e2 in `echo "$events" | tr ',' '\n'`
	do
		echo -e "themeOf\t$e1\t$e2"
		echo -e "causeOf\t$e1\t$e2"
	done
done

echo -e "equivalentTo\tProtein\tProtein"
echo -e "locationOf\tLocalization\tProtein"
echo -e "locationOf\tLocalization\tEntity"
echo -e "partOf\tProtein\tEntity"
echo -e "partOf\tProtein\tProtein"

