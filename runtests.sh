


echo "RUNNING CODE TESTS"
./bin/test > tests/results.txt 

result=$(grep "FAIL" tests/results.txt) 

if  [ "$result" == "" ]; then
    echo "Success!" 
else
    echo "One or more code tests failed. Please see tests/results.txt"
    exit
fi
sleep 1


echo "RUNNING GAME TESTS"
./bin/bzrflag --test --world=tests/test.bzw --red-port=50100 & 

python tests/gametest.py > tests/results.txt

result=$(grep "FAIL" tests/results.txt) 

if  [ "$result" == "" ]; then
    echo "Success!" 
else
    echo "One or more game tests failed. Please see tests/results.txt"
    exit
fi
sleep 1 


echo "Finished!"


