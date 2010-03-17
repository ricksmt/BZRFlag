./bin/bzrflag --world=maps/four_ls.bzw --friendly-fire --red-port=50100 --green-port=50101 --purple-port=50102 --blue-port=50103 $@ &
sleep 5
./shoot_and_capture_agent.py localhost 50100 &
./shoot_and_capture_agent.py localhost 50101 &
./shoot_and_capture_agent.py localhost 50102 &
./shoot_and_capture_agent.py localhost 50103 &

