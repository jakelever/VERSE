#!/bin/bash

testPrefix="test."

dashes="-------------------------------------------------------------------------------------------------"
maxLength=`find $testPrefix* -type f -name '*.sh' | wc -L`

echo ${dashes:1:$maxLength+10}
printf "%"$maxLength"s | %s\n" "Test Name" "Status"
echo ${dashes:1:$maxLength+10}

for test in `find $testPrefix* -type f -name '*.sh' | sort`
do
	printf "%"$maxLength"s | " "$test"
	#echo "Executing $test [ Run $i ]"
	bash $test >/dev/null 2>&1
	retval=$?
	if [[ $retval -eq 0 ]]; then
		echo "pass"
	else
		echo "FAIL"
		
	fi
	
done

echo ${dashes:1:$maxLength+10}
