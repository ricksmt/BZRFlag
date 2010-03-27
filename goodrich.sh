./bin/bzrflag --red-port=54321 --green-port=54320 --world=maps/twoteams.bzw --freeze-tag $@&
sleep 3
python bots/goodrich0.py localhost 54321 &
python bots/goodrich0.py localhost 54320 &

