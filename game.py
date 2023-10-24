import curses
import itertools
import logging
import math
import random
import time

from vector2d import Vector2D

class Globals: pass


class GameObject(object):

  def __init__(self, pos):
    self.pos = pos

  def Update(self): pass

  def Draw(self, stdscr): pass

class Player(GameObject):

  def __init__(self, pos, screen_max):
    super(Player, self).__init__(pos)
    self.screen_max = screen_max
    self.move_dir = 1

  def Update(self):
    # Generate a random movement direction
    # Calculate the new position
    new_x = self.pos.x + self.move_dir
    
    # turn around at the edge
    if new_x >= Globals.screen_size.x -1 or new_x == 0:
      new_x = self.pos.x
      self.move_dir = - self.move_dir

    # Check if the new position is within the terminal boundaries
    self.pos = Vector2D(new_x, self.pos.y)

  def Draw(self, stdscr):
     stdscr.addch(self.pos.y, self.pos.x, '🦍')


class Bridge(GameObject):
  def __init__(self):
    super(Bridge, self).__init__(Vector2D(Globals.screen_size.x, Globals.screen_size.y // 2 + 1))

    self.pieces = [ True for x in range(0, Globals.screen_size.x) ]

  def Draw(self, stdscr):
    for x, piece in zip(itertools.count(), self.pieces):
      this_char = '=' if piece else ' '

      stdscr.addch(self.pos.y, x, this_char)

  def LosePiece(self, x):
    self.pieces[x] = False

class SpaceShip(GameObject):

  MOVING = 1
  SHOOTING = 2

  TIME_MOVING = 100
  TIME_SHOOTING = 20

  def __init__(self, pos):
    super(SpaceShip, self).__init__(pos)
    self.pos = pos
    self.move_dir = 1
    self.image = '<OOO>'
    self.width = len(self.image)//2
    self.time_to_shoot = SpaceShip.TIME_MOVING
    self.time_in_shooting = SpaceShip.TIME_SHOOTING
    self.state = SpaceShip.MOVING

  def Update(self):

    if self.state == SpaceShip.MOVING:
      self.Move()
    elif self.state == SpaceShip.SHOOTING:
      self.Shoot()

  def Move(self):
    # Generate a random movement direction
    # Calculate the new position
    new_x = self.pos.x + self.move_dir
    
    # turn around at the edge
    if new_x == Globals.screen_size.x - self.width - 2 or new_x == 0:
      new_x = self.pos.x
      self.move_dir = - self.move_dir

    # Check if the new position is within the terminal boundaries
    self.pos = Vector2D(new_x, self.pos.y)

    # update time to shoot
    self.time_to_shoot -= 1

    if self.time_to_shoot == 0:
      self.state = SpaceShip.SHOOTING
      self.time_in_shooting = SpaceShip.TIME_SHOOTING


  def Shoot(self):
    self.time_in_shooting -= 1
    if self.time_in_shooting == 0:
      self.time_to_shoot = SpaceShip.TIME_MOVING
      self.state = SpaceShip.MOVING
    # make a laser beam show up here


  def Draw(self, stdscr):
    for dx, char in zip(itertools.count(), self.image):
       stdscr.addch(self.pos.y, self.pos.x + dx, char)

    if (self.state == SpaceShip.SHOOTING 
        and self.time_in_shooting < SpaceShip.TIME_SHOOTING / 2):

      laser_x = self.pos.x + self.width//2+1
      for y in range(self.pos.y+1, Globals.screen_size.y):
        stdscr.addch(y, laser_x, 'X')
      # the bridge loses a piece here
      Globals.bridge.LosePiece(laser_x)



def main(stdscr):
    # Set up the terminal
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Make getch() non-blocking
    stdscr.timeout(20) # Set a delay for getch() in milliseconds

    # Get the terminal size
    sh, sw = stdscr.getmaxyx()
    screen_size= Vector2D(sw, sh)

    Globals.screen_size = screen_size
    logging.info("Screen size is %d, %d", sw, sh)

    # player start pos
    y, x = sh // 2, sw // 2

    Globals.player = Player(Vector2D(x,y), screen_size)
    Globals.bridge = Bridge()
    Globals.ship = SpaceShip(Vector2D(x, 10))

    Globals.all_entities = [Globals.player, Globals.bridge, Globals.ship]

    while True:
        stdscr.clear()

        for entity in Globals.all_entities:
          entity.Update()
          entity.Draw(stdscr)


        # Refresh the screen
        stdscr.refresh()

        # Exit if 'q' is pressed
        # check input
        input_char = stdscr.getch()
        if input_char == ord('q'):
            break
        elif input_char == ord('a'):
          Globals.player.move_dir = - Globals.player.move_dir


        # Sleep for a short time
        #time.sleep(0.01)

if __name__ == "__main__":
    logging.basicConfig(filename='game.log', level=logging.DEBUG)
    curses.wrapper(main)
