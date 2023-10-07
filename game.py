import curses
import itertools
import math
import random
import time

from vector2d import Vector2D

class Player(object):

  def __init__(self, pos, screen_max):
    self.pos = pos
    self.screen_max = screen_max
    self.move_dir = 1

  def Move(self):
    # Generate a random movement direction
    # Calculate the new position
    new_x = self.pos.x + self.move_dir
    
    # turn around at the edge
    if new_x >= self.screen_max.x -2 or new_x == 0:
      new_x = self.pos.x
      self.move_dir = - self.move_dir

    # Check if the new position is within the terminal boundaries
    self.pos = Vector2D(new_x, self.pos.y)

  def Draw(self, stdscr):
     stdscr.addch(self.pos.y, self.pos.x, '🦍')


class Bridge(object):
  def __init__(self, screen_size):
    self.screen_size = screen_size
    self.pieces = [ True for x in range(0, self.screen_size.x) ]

  def Draw(self, stdscr):
    y = self.screen_size.y // 2 + 1
    for x, piece in zip(itertools.count(), self.pieces):
      this_char = '=' if piece else ' '

      stdscr.addch(y, x, this_char)

class SpaceShip(object):

  def __init__(self, pos, screen_max):
    self.pos = pos
    self.screen_max = screen_max
    self.move_dir = 1
    self.image = '<OOO>'
    self.width = len(self.image)//2

  def Move(self):
    # Generate a random movement direction
    # Calculate the new position
    new_x = self.pos.x + self.move_dir
    
    # turn around at the edge
    if new_x == self.screen_max.x - self.width - 2 or new_x == 0:
      new_x = self.pos.x
      self.move_dir = - self.move_dir

    # Check if the new position is within the terminal boundaries
    self.pos = Vector2D(new_x, self.pos.y)

  def Draw(self, stdscr):
    for dx, char in zip(itertools.count(), self.image):
       stdscr.addch(self.pos.y, self.pos.x + dx, char)



def main(stdscr):
    # Set up the terminal
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Make getch() non-blocking
    stdscr.timeout(20) # Set a delay for getch() in milliseconds

    # Get the terminal size
    sh, sw = stdscr.getmaxyx()
    screen_size= Vector2D(sw, sh)

    # player start pos
    y, x = sh // 2, sw // 2

    player = Player(Vector2D(x,y), screen_size)
    bridge = Bridge(screen_size)
    ship = SpaceShip(Vector2D(x, 10), screen_size)

    while True:
                # Clear the screen
        stdscr.clear()

        bridge.Draw(stdscr)

        player.Move()
        player.Draw(stdscr)

        ship.Move()
        ship.Draw(stdscr)



        # Refresh the screen
        stdscr.refresh()

        # Exit if 'q' is pressed
        # check input
        input_char = stdscr.getch()
        if input_char == ord('q'):
            break
        elif input_char == ord('a'):
          player.move_dir = - player.move_dir


        # Sleep for a short time
        #time.sleep(0.01)

if __name__ == "__main__":
    curses.wrapper(main)
