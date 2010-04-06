#!/usr/bin/python -tt

from bzrc import BZRC, GoodrichCommand, Answer
import sys, math, time, random

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
        self.update()
        self.past_position = {}
        self.goals = {}
        self.stuck = {}
        for tank in self.mytanks:
            self.past_position[tank.index] = tank.x, tank.y
            self.goals[tank.index] = None
            self.stuck[tank.index] = 0
        self.set_flag_goals()

    def update(self):
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        self.othertanks = othertanks
        self.flags = flags
        #occg = list(self.bzrc.get_occgrid(i.index) for i in self.mytanks)

    def set_flag_goals(self):
        for tank in self.mytanks:
            best = [0,None]
            flag = self.closest_flag(tank)
            if flag:
                self.goals[tank.index] = flag.x,flag.y

    def tick(self, time_diff):
        '''Some time has passed; decide what to do next'''
        # Get information from the BZRC server
        self.update()

        # Reset my set of commands (we don't want to run old commands)
        self.commands = []

        # Decide what to do with each of my tanks
        for bot in self.mytanks:
            self.update_goal(bot)
            self.past_position[bot.index] = bot.x, bot.y

        # Send the commands to the server
        results = self.bzrc.do_commands(self.commands)

    def update_goal(self, bot):
        if bot.flag != '-':
            self.goals[bot.index] = self.base.x, self.base.y
        if not self.goals[bot.index]:
            flag = self.closest_flag(bot)
            if flag:
                self.goals[bot.index] = flag.x, flag.y
            else:
                self.goals[bot.index] = self.random_pos()
        elif (bot.x, bot.y) == self.past_position[bot.index]:
            self.goals[bot.index] = self.random_pos()

        x,y = self.goals[bot.index]
        dx = x - bot.x
        dy = y - bot.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist < 10:
            self.goals[bot.index] = None
            return
        self.commands.append(GoodrichCommand(bot.index, dx/5, dy/5))

    def random_pos(self):
        width = int(self.constants['worldsize'])
        x = random.randrange(width) - width/2
        y = random.randrange(width) - width/2
        return x,y

    def closest_flag(self, bot):
        best = None
        for flag in self.flags:
            if flag.color == self.constants['team']:
                continue
            if flag.poss_color != 'none':
                continue
            dist = math.sqrt((flag.x - bot.x)**2 + (flag.y - bot.y)**2)
            if not best or dist < best[0]:
                best = [dist, flag]
        if best:
            return best[1]

    def move_towards(self, bot, x, y):
        dx = x - bot.x
        dy = y - bot.y
        self.commands.append(GoodrichCommand(bot.index, dx/10, dy/10))

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
