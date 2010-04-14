./bin/bzrflag --world=maps/four_ls.bzw --friendly-fire --red-port=50100 --green-port=50101 --purple-port=50102 --blue-port=50103 $@ &
sleep 5
python bots/compiled/blind.py agent2 localhost 50100 &
python bots/compiled/blind.py agent1 localhost 50101 &
python bots/compiled/blind.py agent1 localhost 50102 &
python bots/compiled/blind.py agent1 localhost 50103 &

