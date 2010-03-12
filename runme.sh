./bin/bzrflag --world=maps/simple.bzw --red-port=50100 --green-port=50101 --purple-port=50102 --blue-port=50103 &
sleep 4
./sync.py localhost 50100 &
./sync.py localhost 50101 &
./sync.py localhost 50102 &
./sync.py localhost 50103 &

