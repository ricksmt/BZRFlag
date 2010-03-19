#!/usr/bin/python -tt

# In this agent, half of the tanks behave exactly as in agent0, and half of the
# tanks find the nearest flag and try to capture it.

from bzrc import BZRC, Command, Answer, normalize_angle
import sys, math


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
    my_color = constants['team']

    flags = bzrc.get_flags()
    for flag in flags:
        if flag.color == my_color:
            my_base = Answer()
            my_base.x = flag.x
            my_base.y = flag.y

    try:
        while True:
            mytanks, othertanks, flags, shots = bzrc.get_lots_o_stuff()
            enemies = [tank for tank in othertanks if tank.color !=
                    constants['team']]

            commands = []
            numtanks = len(mytanks)
            attackers = mytanks[:int(numtanks/2)]
            flag_getters = mytanks[int(numtanks/2):]
            for bot in attackers:
                if bot.flag != '-':
                    target_angle = math.atan2(my_base.y - bot.y,
                            my_base.x - bot.x)
                    relative_angle = normalize_angle(target_angle - bot.angle)
                    command = Command(bot.index, 1, 2 * relative_angle, True)
                    commands.append(command)
                    continue
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

            for bot in flag_getters:
                if bot.flag != '-':
                    target_angle = math.atan2(my_base.y - bot.y,
                            my_base.x - bot.x)
                    relative_angle = normalize_angle(target_angle - bot.angle)
                    command = Command(bot.index, 1, 2 * relative_angle, True)
                    commands.append(command)
                    continue
                best_flag = None
                best_dist = 2 * float(constants['worldsize'])
                for flag in flags:
                    if flag.color == my_color:
                        continue
                    if flag.poss_color != 'none':
                        continue
                    dist = math.sqrt((flag.x - bot.x)**2 + (flag.y - bot.y)**2)
                    if dist < best_dist:
                        best_dist = dist
                        best_flag = flag
                if best_flag is None:
                    command = Command(bot.index, 0, 0, False)
                else:
                    target_angle = math.atan2(best_flag.y - bot.y,
                            best_flag.x - bot.x)
                    relative_angle = normalize_angle(target_angle - bot.angle)
                    command = Command(bot.index, 1, 2 * relative_angle, True)
                    commands.append(command)

            results = bzrc.do_commands(commands)
            for bot, result in zip(mytanks, results):
                did_speed, did_angvel, did_shot = result
                if did_shot:
                    print 'Shot fired by tank #%s (%s)' % (bot.index,
                            bot.callsign)


    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4
