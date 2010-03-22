#!/usr/bin/python -tt

from bzrc import BZRC, Command, Answer
import sys, math, time

# In this agent, half of the tanks behave exactly as in agent0, and half of the
# tanks find the nearest flag and try to capture it.

class Agent(object):

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []
        bases = self.bzrc.get_bases()
        for base in bases:
            if base.color == self.constants['team']:
                self.base = Answer()
                self.base.x = (base.corner1_x+base.corner3_x)/2
                self.base.y = (base.corner1_y+base.corner3_y)/2

    def tick(self, time_diff):
        '''Some time has passed; decide what to do next'''
        # Get information from the BZRC server
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                self.constants['team']]

        # Reset my set of commands (we don't want to run old commands)
        self.commands = []

        # Decide what to do with each of my tanks
        numtanks = len(mytanks)
        attackers = mytanks[:int(numtanks/2)]
        flag_getters = mytanks[int(numtanks/2):]
        for bot in attackers:
            self.attack_enemies(bot)
        for bot in flag_getters:
            self.get_flag(bot)

        # Send the commands to the server
        results = self.bzrc.do_commands(self.commands)

    def attack_enemies(self, bot):
        '''Find the closest enemy and chase it, shooting as you go'''
        if bot.flag != '-':
            self.move_to_position(bot, self.base.x, self.base.y)
            return
        best_enemy = None
        best_dist = 2 * float(self.constants['worldsize'])
        for enemy in self.enemies:
            try:
                if enemy.status != 'alive':
                    continue
            except AttributeError:
                print vars(enemy)
                exit(0)
            dist = math.sqrt((enemy.x - bot.x)**2 + (enemy.y - bot.y)**2)
            if dist < best_dist:
                best_dist = dist
                best_enemy = enemy
        if best_enemy is None:
            command = Command(bot.index, 0, 0, False)
            self.commands.append(command)
        else:
            self.move_to_position(bot, best_enemy.x, best_enemy.y)

    def get_flag(self, bot):
        if bot.flag != '-':
            self.move_to_position(bot, self.base.x, self.base.y)
            return
        best_flag = None
        best_dist = 2 * float(self.constants['worldsize'])
        for flag in self.flags:
            if flag.color == self.constants['team']:
                continue
            if flag.poss_color != 'none':
                continue
            dist = math.sqrt((flag.x - bot.x)**2 + (flag.y - bot.y)**2)
            if dist < best_dist:
                best_dist = dist
                best_flag = flag
        if best_flag is None:
            self.attack_enemies(bot)
        else:
            self.move_to_position(bot, best_flag.x, best_flag.y)

    def move_to_position(self, bot, target_x, target_y):
        target_angle = math.atan2(target_y - bot.y,
                target_x - bot.x)
        relative_angle = self.normalize_angle(target_angle - bot.angle)
        command = Command(bot.index, 1, 2 * relative_angle, True)
        self.commands.append(command)

    def normalize_angle(self, angle):
        '''Make any angle be between +/- pi.'''
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle


def main():
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

    agent = Agent(bzrc)

    prev_time = time.time()

    # Run the agent
    try:
        while True:
            time_diff = time.time() - prev_time
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4
