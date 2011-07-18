#!/usr/bin/env python

import magictest
import serverlink

link = None

class TestCommands(magictest.MagicTest):

    def setUp(self): 
        global link
        self.host = "localhost"
        self.port = 50100
        if link is None:
            link = serverlink.Link(self.host, self.port) 
        
        
    def tearDown(self):
        pass

    # Commands tests
    def test_help(self):
        link.sendline('help')
        response = link.read_arr()
        print response
        #self.assertIn(':speed', response)
        self.assertIn(':angvel', response)
            
    def test_bases(self):
       print "pass"
       
    def test_constants(self):
       print "pass"
       
    def test_flags(self):
       print "pass"
       
    def test_angvel(self):
       print "pass"
    
    def test_mytanks(self):
       print "pass" 
       
    def test_obstacles(self):
       print "pass" 
       
    def test_occupancy_grid(self):
       print "pass" 
       
    def test_othertanks(self):
       print "pass"  
       
    def test_quit(self):
       print "pass" 
   
    def test_scores(self):
       print "pass"
       
    def test_shoot(self):
       print "pass"
       
    def test_shots(self):
       print "pass"
       
    def test_speed(self):
       print "pass"
   
    def test_teams(self):
       print "pass"
       
    def test_timer(self):
       print "pass"
       
    def test_endgame(self):
       print "pass"
       
               
def run(vb=2):
    global link
    result = TestCommands.runSuite(vb)
    link.sendline('endgame')
    link = None
    return result


# vim: et sw=4 sts=4
