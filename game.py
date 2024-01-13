import curses
from dataclasses import dataclass
import itertools
import logging
import math
import pdb
import random
import time

from vector2d import Vector2D

class GameState: 

  START_SCREEN = 0
  PLAYING = 1
  FALLING = 2 # when one player hits the bottom, now everthing falls down
  WIN_SCREEN = 3 # when one player was won
  EXIT = -1

  def __init__(self):
    self.all_entities = set()
    self.to_remove = set()
    self.to_add = set()
    self.stdscr = None # this will get set later
    self.state = GameState.START_SCREEN
    self.player_1_lives = 3
    self.player_2_lives = 3
    self.new_events = []
    self.historical_events = [] # this only grows over time, for debugging
    self.turn_counter = 0
  
  def HandleEvent(self, event):
    """Some game state logic happens because of globally published messages"""

    logging.info("Event: %s", event)
    self.new_events.append(event)
    self.historical_events.append(event)

    if isinstance(event, PlayerFallingEvent):
      self.state = GameState.FALLING
    elif isinstance(event, PlayerFallingCompleteEvent):
      self.state = GameState.PLAYING
    elif isinstance(event, GameStartEvent):
      self._HandleGameStartEvent()

  def _HandleGameStartEvent(self):
    # clear out all the enetities
    self.all_entities = set()

    x = self.screen_size.x //2
    y = self.screen_size.y // 2
    self.bridge = Bridge()
    self.ship = SpaceShip(Vector2D(x, 8))
    self.player_1 = Player(Vector2D(x // 2, y), '🦍')
    self.player_2 = Player(Vector2D(x + x // 2, y), '🦫')

    for ent in [
      self.player_1,
      self.player_2,
      self.bridge,
      self.ship,
      PlayerLifeCounter(self.player_1, 0),
      PlayerLifeCounter(self.player_2, self.screen_size.x - 6),
      GameNarratorDisplay()
    ]:
     self.AddEntity(ent)

  def Update(self):
    # first update all the entities
    for entity in self.all_entities:
      entity.Update()

   # now handle all the new events
    for event in self.new_events:
      for entity in self.all_entities:
        entity.HandleEvent(event)

    # update entity sets and turn counters
    self.all_entities = list(set(self.all_entities).union(self.to_add).difference(self.to_remove))
    self.to_remove = set()
    self.to_add = set()
    self.new_events = []
    self.turn_counter += 1 

  def Draw(self):
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
     elif input_char == ord(' '):
       # for now just leave this on
       if True or (self.state == GameState.START_SCREEN):
         self.HandleEvent(GameStartEvent())
     elif input_char == ord('d'):
       curses.curs_set(1)  # Hide the cursor
       self.stdscr.clear()
       self.stdscr.refresh()
       pdb.set_trace()




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

  def HandleEvent(self, event): pass

  def _BroadcastEvent(self, event):
    game_state.HandleEvent(event)

  def Draw(self, stdscr): pass

  def Die(self):
    game_state.RemoveEntity(self)

class Player(GameObject):

  PLAYING = 0
  FALLING = 1
  EXPLODING = 2
  WINNING = 3

  def __init__(self, pos, icon):
    super(Player, self).__init__(pos)
    self.move_dir = 1
    self.state = Player.PLAYING
    self.icon = icon
    self.lives = 1

    # for jumping
    self.bridge_height = game_state.bridge.pos.y-1
    self.jump_height = self.bridge_height - 4
    self.jump_dir = -1

  def Update(self):
    # if someone is falling, we stop moving
    if self.state == Player.PLAYING and not game_state.state == GameState.FALLING:
      self.UpdatePlaying()
    elif self.state == Player.FALLING:
      self.UpdateFalling()
    elif self.state == Player.EXPLODING:
      self.UpdateExploding()
    elif self.state == Player.WINNING:
      self.UpdateWinning()

  def HandleEvent(self, event):
    if isinstance(event, PlayerFallingCompleteEvent) and event.player == self:
      self.state = Player.PLAYING
      self.lives -= 1
      if self.lives == 0:
        self._BroadcastEvent(PlayerLosesEvent(player=self))
        self.state = Player.EXPLODING

    elif isinstance(event, PlayerLosesEvent):
      if event.player == self:
        self.state = Player.EXPLODING
      else:
        self.state = Player.WINNING


  def UpdateFalling(self):
    # keep falling down until you hit the bottom of the screen
    self.pos = self.pos + Vector2D(0,1)

    if (self.pos.y == game_state.screen_size.y):
      self.pos.y = 0

    # we've wrapped around and hit the bridge 
    # we are no longer falling
    if (self.pos.y == game_state.bridge.pos.y-1):
      self._BroadcastEvent(PlayerFallingCompleteEvent(player=self))

  def UpdatePlaying(self):
    # check to see if the player is about to fall off the bridge
    if (not game_state.bridge.HasPiece(self.pos.x)):
      self.state = Player.FALLING
      self._BroadcastEvent(PlayerFallingEvent(player=self))
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


  def UpdateExploding(self):
    pass

  def UpdateWinning(self):
    # jump up and down here
    if self.jump_dir == -1:
      self.pos.y = self.pos.y - 1
      if self.pos.y <= self.jump_height:
        self.jump_dir = 1
    else:
      self.pos.y = self.pos.y + 1
      if self.pos.y >= self.bridge_height:
        self.jump_dir = -1


  def Draw(self, stdscr):
     stdscr.addch(self.pos.y, self.pos.x, self.icon)


class PlayerLifeCounter(GameObject):

  def __init__(self, player, x_position):
    self.player = player
    self.is_losing_life = False
    self.x_position = x_position

  def Draw(self, stdscr):
    # draw player life count
    num_to_draw = self.player.lives

    # possibly add one if we are blinking now
    if (self.is_losing_life):
      if (game_state.turn_counter % 20 > 10):
        num_to_draw -= 1

    for x in range(num_to_draw):
      stdscr.addch(0, self.x_position + x, self.player.icon)


  def HandleEvent(self, event):
    if isinstance(event, PlayerFallingEvent) and event.player == self.player:
      self.is_losing_life = True
    if isinstance(event, PlayerFallingCompleteEvent):
      self.is_losing_life = False

class GameNarratorDisplay(GameObject):

  def __init__(self):
    super(GameNarratorDisplay, self).__init__(Vector2D(game_state.screen_size.x//2, 4))

    self.message = ''

  def Draw(self, stdscr):
    # draw player life count
    start_x = self.pos.x - len(self.message)//2
    for i, c in enumerate(self.message):
      stdscr.addch(self.pos.y, start_x + i, c)


  def HandleEvent(self, event):
    if isinstance(event, PlayerLosesEvent) :
      winner = game_state.player_1 if event.player == game_state.player_2 else game_state.player_2
      self.message = f'{event.player.icon} Has Died! {winner.icon} Wins!'



class Bridge(GameObject):
  def __init__(self):
    super(Bridge, self).__init__(Vector2D(game_state.screen_size.x, game_state.screen_size.y // 2 + 1))
    self.ResetAllPieces()


  def Draw(self, stdscr):
    for x, piece in zip(itertools.count(), self.pieces):
      this_char = '=' if piece else ' '

      stdscr.addch(self.pos.y, x, this_char)

  def HandleEvent(self, event):
    if isinstance(event, PlayerFallingCompleteEvent):
      self.ResetAllPieces()


  def ResetAllPieces(self):
    self.pieces = [ True for x in range(0, game_state.screen_size.x) ]

  def LosePiece(self, x):
    self.pieces[x] = False

  def HasPiece(self, x):
    return self.pieces[x]


class SpaceShip(GameObject):

  MOVING = 1
  SHOOTING = 2
  END_GAME = 3

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
    elif self.state == SpaceShip.END_GAME:
      self.time_to_shoot = 100
      self.Move()

  def HandleEvent(self, event):
    if isinstance(event, GameStartEvent):
      self.state = SpaceShip.MOVING
    elif isinstance(event, PlayerLosesEvent):
      self.state = SpaceShip.END_GAME
   

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


# messages

@dataclass
class GameStartEvent:

  def __repr__(self):
    return '[Event: game begins!]'

@dataclass
class PlayerFallingEvent:
  player: Player

  def __repr__(self):
    return f"[Event: {self.player.icon} is falling]"

@dataclass
class PlayerFallingCompleteEvent:
  player: Player

  def __repr__(self):
    return f"[Event: {self.player.icon} is done falling]"

@dataclass
class PlayerLosesEvent:
  player: Player

  def __repr__(self):
    return f"[Event: {self.player.icon} has lost the game]"



@dataclass
class DebugRequest:
  def __repr__(self):
    return "[Event: DebugRequest]"

def main(stdscr):
    # Set up the terminal
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Make getch() non-blocking
    stdscr.timeout(20) # Set a delay for getch() in milliseconds

    game_state.stdscr = stdscr

    # Get the terminal size
    sh, sw = stdscr.getmaxyx()
    screen_size = Vector2D(sw, sh)
    game_state.screen_size = screen_size
    logging.info("Screen size is %d, %d", sw, sh)

    narrator = GameNarratorDisplay()
    narrator.message = 'Press Space To Begin.'
    game_state.AddEntity(narrator)

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
