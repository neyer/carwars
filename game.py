import curses
import itertools
import logging
import math
import random
import time

from vector2d import Vector2D


class GameState: 

  def __init__(self):
    self.all_entities = set()
    self.to_remove = set()
    self.to_add = set()

  def Update(self):
    for entity in self.all_entities:
      entity.Update()
    self.all_entities = (self.all_entities.union(self.to_add)).difference(self.to_remove)
    self.to_remove = set()
    self.to_add = set()

  def Draw(self, stdscr):
    for entity in self.all_entities:
      entity.Draw(stdscr)


  def AddEntity(self, entity):
    assert(entity is not None)
    self.to_add.add(entity)

  def RemoveEntity(self, entity):
    self.to_remove.add(entity)


game_state = GameState()



class GameObject(object):

  def __init__(self, pos):
    self.pos = pos

  def Update(self): pass

  def Draw(self, stdscr): pass

  def Die(self):
    game_state.RemoveEntity(self)

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
    if new_x >= game_state.screen_size.x -1 or new_x == 0:
      new_x = self.pos.x
      self.move_dir = - self.move_dir

    # Check if the new position is within the terminal boundaries
    self.pos = Vector2D(new_x, self.pos.y)

  def Draw(self, stdscr):
     stdscr.addch(self.pos.y, self.pos.x, '🦍')


class Bridge(GameObject):
  def __init__(self):
    super(Bridge, self).__init__(Vector2D(game_state.screen_size.x, game_state.screen_size.y // 2 + 1))

    self.pieces = [ True for x in range(0, game_state.screen_size.x) ]

  def Draw(self, stdscr):
    for x, piece in zip(itertools.count(), self.pieces):
      this_char = '=' if piece else ' '

      stdscr.addch(self.pos.y, x, this_char)

  def LosePiece(self, x):
    self.pieces[x] = False

class SpaceShip(GameObject):

  MOVING = 1
  SHOOTING = 2

  TIME_MOVING = 50
  TIME_SHOOTING = 10

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
    if new_x == game_state.screen_size.x - self.width - 2 or new_x == 0:
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

      game_state.AddEntity(LaserBeam(self.pos + Vector2D(self.width,1)))


  def Draw(self, stdscr):
    for dx, char in zip(itertools.count(), self.image):
       stdscr.addch(self.pos.y, self.pos.x + dx, char)



class LaserBeam(GameObject):

  def __init__(self, pos):
    super(LaserBeam, self).__init__(pos)
   

  def Update(self):
      self.Move()

  def Move(self):
    # Generate a random movement direction
    # Calculate the new position
    new_y = self.pos.y + 1

    if (new_y == game_state.bridge.pos.y):
      game_state.bridge.LosePiece(self.pos.x)
      self.Die()

    if (new_y == game_state.screen_size.y):
      # time do die
      self.Die()
    
    self.pos = Vector2D(self.pos.x, new_y)
    
  def Draw(self, stdscr):
     stdscr.addch(self.pos.y, self.pos.x, '*')

     # the bridge loses a piece here




def main(stdscr):
    # Set up the terminal
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Make getch() non-blocking
    stdscr.timeout(20) # Set a delay for getch() in milliseconds

    # Get the terminal size
    sh, sw = stdscr.getmaxyx()
    screen_size= Vector2D(sw, sh)

    game_state.screen_size = screen_size
    logging.info("Screen size is %d, %d", sw, sh)

    # player start pos
    y, x = sh // 2, sw // 2

    game_state.player = Player(Vector2D(x,y), screen_size)
    game_state.bridge = Bridge()
    game_state.ship = SpaceShip(Vector2D(x, 10))
    
    for ent in [game_state.player, game_state.bridge, game_state.ship]:
      game_state.AddEntity(ent)

    while True:
        stdscr.clear()

        game_state.Update()
        game_state.Draw(stdscr)


        # Refresh the screen
        stdscr.refresh()

        # Exit if 'q' is pressed
        # check input
        input_char = stdscr.getch()
        if input_char == ord('q'):
            break
        elif input_char == ord('a'):
          game_state.player.move_dir = - game_state.player.move_dir


        # Sleep for a short time
        #time.sleep(0.01)

if __name__ == "__main__":
    logging.basicConfig(filename='game.log', level=logging.DEBUG)
    curses.wrapper(main)
