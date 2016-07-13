#!/bin/bash

testPrefix="BioNLP16."

outDir=tmp.Logs
rm -fr $outDir
mkdir $outDir

dashes="-------------------------------------------------------------------------------------------------"
maxLength=`find $testPrefix* -type f -name '*.sh' | wc -L`

echo ${dashes:1:$maxLength+10}
printf "%"$maxLength"s | %s\n" "Test Name" "Status"
echo ${dashes:1:$maxLength+10}

for test in `find $testPrefix* -type f -name '*.sh' | sort | grep -v -F "BioNLP16.GE4.sh"`
do
	base=`basename $test`
	log=$outDir/$base.log
	
	printf "%"$maxLength"s | " "$test"
	#echo "Executing $test [ Run $i ]"
	bash $test > $log 2>&1
	retval=$?
	if [[ $retval -eq 0 ]]; then
		echo "pass"
	else
		echo "FAIL"
	fi
	
done

echo ${dashes:1:$maxLength+10}
