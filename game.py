import curses
import itertools
import logging
import math
import random
import time

from vector2d import Vector2D


class GameState: 


  PLAYING = 1
  FALLING = 2 # when one player hits the bottom, now everthing falls down
  EXIT = -1

  def __init__(self):
    self.all_entities = set()
    self.to_remove = set()
    self.to_add = set()
    self.stdscr = None # this will get set later
    self.state = GameState.PLAYING
    self.player_1_lives = 3
    self.player_2_lives = 3

  def Update(self):
    for entity in self.all_entities:
      entity.Update()
    self.all_entities = (self.all_entities.union(self.to_add)).difference(self.to_remove)
    self.to_remove = set()
    self.to_add = set()

  def Draw(self):

    # draw player life count
    for x in range(self.player_1_lives):
      self.stdscr.addch(0, x, self.player_1.icon)

    for x in range(self.player_2_lives):
      # need some offset on the right side
      # 'screen size' does some weird things with the scroll bar
      self.stdscr.addch(0, self.screen_size.x - 6 + x, self.player_2.icon)

    for entity in self.all_entities:
      entity.Draw(self.stdscr)

  def HandleInput(self):
    # Exit if 'q' is pressed
     # check input
     input_char = self.stdscr.getch()
     if input_char == ord('q'):
       self.state = GameState.EXIT
     elif input_char == ord('a'):
       self.player_1.move_dir = - game_state.player_1.move_dir
     elif input_char == ord('l'):
       self.player_2.move_dir = - game_state.player_2.move_dir



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

  PLAYING = 0
  FALLING = 1

  def __init__(self, pos, icon):
    super(Player, self).__init__(pos)
    self.move_dir = 1
    self.state = Player.PLAYING
    self.icon = icon

  def Update(self):
    if self.state == Player.PLAYING:
      self.UpdatePlaying()
    elif self.state == Player.FALLING:
      self.UpdateFalling()

  def UpdateFalling(self):
    # keep falling down until you hit the bottom of the screen
    self.pos = self.pos + Vector2D(0,1)

    if (self.pos.y == game_state.screen_size.y):
      self.pos.y = 0

  def UpdatePlaying(self):
    # check to see if the player is about to fall off the bridge
    if (not game_state.bridge.HasPiece(self.pos.x)):
      self.state = Player.FALLING
      return

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
     stdscr.addch(self.pos.y, self.pos.x, self.icon)


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

  def HasPiece(self, x):
    return self.pieces[x]


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

    game_state.stdscr = stdscr

    # Get the terminal size
    sh, sw = stdscr.getmaxyx()
    screen_size= Vector2D(sw, sh)

    game_state.screen_size = screen_size
    logging.info("Screen size is %d, %d", sw, sh)

    # player start pos
    y, x = sh // 2, sw // 2

    game_state.player_1 = Player(Vector2D(x//2,y),  '🦍')
    game_state.player_2 = Player(Vector2D(x + x//2,y), '🦫')
    game_state.bridge = Bridge()
    game_state.ship = SpaceShip(Vector2D(x, 10))
    
    for ent in [game_state.player_1, game_state.player_2, game_state.bridge, game_state.ship]:
      game_state.AddEntity(ent)

    while game_state.state != GameState.EXIT:
        stdscr.clear()

        game_state.Update()

        # Refresh the screen and draw
        game_state.Draw()
        stdscr.refresh()

        game_state.HandleInput()

        # Sleep for a short time
        #time.sleep(0.01)

if __name__ == "__main__":
    logging.basicConfig(filename='game.log', level=logging.DEBUG)
    curses.wrapper(main)
