


echo "RUNNING CODE TESTS"
./bin/codetests > tests/results.txt 

result=$(grep "FAIL" tests/results.txt) 

if  [ "$result" == "" ]; then
    echo "Success!" 
else
    echo "One or more code tests failed. Please see tests/results.txt"
    exit
fi
sleep 1


echo "RUNNING GAME TESTS"
./bin/bzrflag --test --world=tests/gametests/test.bzw --red-port=50100 & 

./bin/gametests > tests/results.txt

result=$(grep "FAIL" tests/results.txt) 

if  [ "$result" == "" ]; then
    echo "Success!" 
else
    echo "One or more game tests failed. Please see tests/results.txt"
    exit
fi
sleep 1 


echo "Finished!"


