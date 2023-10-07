import curses
import random
import time
import math

class Vector2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2D(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar):
        return Vector2D(self.x / scalar, self.y / scalar)

    def __str__(self):
        return f"({self.x}, {self.y})"

    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            return Vector2D(0, 0)
        return self / mag

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
    if new_x == self.screen_max.x -2 or new_x == 0:
      self.move_dir = - self.move_dir

    # Check if the new position is within the terminal boundaries
    self.pos = Vector2D(new_x, self.pos.y)




def main(stdscr):
    # Set up the terminal
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Make getch() non-blocking
    stdscr.timeout(10) # Set a delay for getch() in milliseconds

    # Get the terminal size
    sh, sw = stdscr.getmaxyx()
    # Initial position of the dot
    y, x = sh // 2, sw // 2
    player = Player(Vector2D(x,y), Vector2D(sw, sh))

    while True:
                # Clear the screen
        stdscr.clear()

        player.Move()

        # Display the dot at the new position
        stdscr.addch(player.pos.y, player.pos.x, '🦍')

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
