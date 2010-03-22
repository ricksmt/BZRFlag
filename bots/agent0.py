#!/usr/bin/python -tt

from bzrc import BZRC, Command, normalize_angle
import sys, math

# An incredibly simple agent.  All we do is find the closest enemy tank, drive
# towards it, and shoot.  Note that if friendly fire is allowed, you will very
# often kill your own tanks with this code.

#################################################################
# NOTE TO STUDENTS
# This is a starting point for you.  You will need to greatly
# modify this code if you want to do anything useful.  But this
# should help you to know how to interact with BZRC in order to
# get the information you need.
# 
# After starting the bzrflag server, this is one way to start
# this code:
# python agent0.py [hostname] [port]
# 
# Often this translates to something like the following (with the
# port name being printed out by the bzrflag server):
# python agent0.py localhost 49857
#################################################################

def main():
    ########################################################################

    # Process CLI arguments.

    try:
        execname, host, port = sys.argv
    except ValueError:
        execname = sys.argv[0]
        print >>sys.stderr, '%s: incorrect number of arguments' % execname
        print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
        sys.exit(-1)

    # Connect.

    #bzrc = BZRC(host, int(port), debug=True)
    bzrc = BZRC(host, int(port))

    constants = bzrc.get_constants()

    try:
        while True:
            mytanks, othertanks, flags, shots = bzrc.get_lots_o_stuff()
            enemies = [tank for tank in othertanks if tank.color !=
                    constants['team']]

            commands = []
            for bot in mytanks:
                best_enemy = None
                best_dist = 2 * float(constants['worldsize'])
                for enemy in enemies:
                    if enemy.status != 'alive':
                        #print 'notnormal',enemy,enemy.status
                        break
                    dist = math.sqrt((enemy.x - bot.x)**2 +
                            (enemy.y - bot.y)**2)
                    if dist < best_dist:
                        best_dist = dist
                        best_enemy = enemy

                if best_enemy is None:
                    command = Command(bot.index, 0, 0, False)
                else:
                    target_angle = math.atan2(best_enemy.y - bot.y,
                            best_enemy.x - bot.x)
                    relative_angle = normalize_angle(target_angle - bot.angle)
                    command = Command(bot.index, 1, 2 * relative_angle, True)
                    commands.append(command)

            results = bzrc.do_commands(commands)
            for bot, result in zip(mytanks, results):
                did_speed, did_angvel, did_shot = result
                if did_shot:
                    print 'shot fired by tank #%s (%s)' % (bot.index,
                            bot.callsign)


    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4
