./bin/bzrflag --world=maps/four_ls.bzw --friendly-fire --red-port=50100 --green-port=50101 --purple-port=50102 --blue-port=50103 $@ &
sleep 5
./bots/compiled/blind.py agent1.py localhost 50100 &
./bots/compiled/blind.py agent1.py localhost 50101 &
./bots/compiled/blind.py agent1.py localhost 50102 &
./bots/compiled/blind.py agent1.py localhost 50103 &

