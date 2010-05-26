./bin/bzrflag --world=maps/tricky_occgrid.bzw --friendly-fire --red-port=50101 --default-true-positive=.95 --default-true-negative=.95 --occgrid-width=100 --no-report-obstacles --red-tanks=5 $@ &
sleep 3
python bots/compiled/blind.py grid_lab_agent localhost 50101 &

