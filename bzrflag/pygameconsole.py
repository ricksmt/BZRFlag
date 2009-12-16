import pygame
from pygame.locals import *

from code import InteractiveConsole as IC
import string
import sys

class Console:
    def __init__(self, game, rect):
        self.console = IC({'game':game,'sys':sys,'pygame':pygame,'self':self,'purple':game.map.teams['purple']})
        self.rect = pygame.Rect(rect)
        self.minrect = pygame.Rect(self.rect.bottom-30,self.rect.right-30,30,30)
        self.image = pygame.Surface(self.rect.size)
        #self.image.set_alpha(100)
        self.dirty = True
        self.txt = ''
        self.game = game
        self.font = pygame.font.Font(None,20)
        self.lineheight = 15
        self.history = []
        self.minimized = True
        self.athistory = 0
        self.bgc = (0,110,7)
        self.prompt()

    def write(self, text):
        self.txt += text
        self.dirty = True

    def prompt(self):
        self.txt += '>>> '
        self.index = len(self.txt)

    def render(self):
        if not self.dirty:return
        self.image.fill(self.bgc)#006E0700))
        for i,line in enumerate(self.txt.split('\n')[-10:]):
            self.image.blit(self.font.render(line,1,(0,0,0),self.bgc),(10,self.lineheight*i+10))
        nrect = pygame.Rect(self.minrect)
        nrect.bottomright = self.rect.size
        pygame.draw.rect(self.image, (255,255,255), nrect)
        pygame.draw.rect(self.image, self.bgc, nrect.inflate(-6,-6))
        self.dirty = False

    def draw(self, screen):
        if self.minimized:
            pygame.draw.rect(screen, (255,255,255), self.minrect)
            pygame.draw.rect(screen, self.bgc, self.minrect.inflate(-6,-6))
        else:
            self.render()
            screen.blit(self.image, self.rect)

    def execute(self):
        next = self.txt[self.index:]
        self.athistory = len(self.history)+1
        self.history.append(next)
        self.txt += '\n'
        sys.stderr = self
        sys.stdout = self
        self.console.push(next+'\n')
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stdout__
        self.prompt()

    def rehistory(self):
        if 0 <= self.athistory < len(self.history):
            self.txt = self.txt[:self.index] + self.history[self.athistory]
        else:
            if self.athistory < -1:
                self.athistory = -1
            if self.athistory > len(self.history):
                self.athistory = len(self.history)
            self.txt = self.txt[:self.index]

    def event(self, e):
        if e.type == KEYDOWN:
            if self.minimized:return
            if e.key == 8:
                if len(self.txt)>self.index:
                    self.txt = self.txt[:-1]
            elif e.key == 13:
                self.execute()
            elif e.key == K_UP:
                self.athistory -= 1
                self.rehistory()
            elif e.key == K_DOWN:
                self.athistory += 1
                self.rehistory()
            elif e.unicode in string.printable:
                self.txt += e.unicode
            else:return
            self.dirty = True
        elif e.type == MOUSEBUTTONDOWN:
            if self.minrect.collidepoint(e.pos):
                self.minimized = not self.minimized
                if self.minimized:
                    self.game.display.redraw()
