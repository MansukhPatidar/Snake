import curses
from curses.textpad import rectangle
import time
from enum import Enum
import random
from playsound import playsound


class PartType(Enum):
    Head = 0
    Body = 1
    Tail = 2


class DIRECTION(Enum):
    Left = 0
    Right = 1
    Up = 2
    Down = 3


class Position:
    x = 0
    y = 0

    def __init__(self, x, y):
        self.x = x
        self.y = y


class SnakePart:
    position = Position(0, 0)
    _type = PartType.Body

    def __init__(self, pos):
        self.position = pos

    def set_type(self, _type):
        self._type = _type

    def get_char(self):
        return ['*', curses.ACS_DIAMOND, curses.ACS_DIAMOND][int(self._type.value)]

    def draw(self, screen):
        screen.addch(self.position.y, self.position.x, self.get_char())

    def erase(self, screen):
        screen.addstr(self.position.y, self.position.x, ' ')

    def hit_test(self, pos):
        return self.position.x == pos.x and self.position.y == pos.y


class SnakeFood(SnakePart):
    def draw(self, screen):
        screen.addstr(self.position.y, self.position.x,
                      '*', curses.color_pair(2))


class Snake():
    parts = []

    def len(self):
        return len(self.parts)

    def update_parttype(self):
        for i in range(self.len()):
            _type = PartType.Body

            if i == 0:
                _type = PartType.Tail

            if i == self.len()-1:
                _type = PartType.Head

            self.parts[i].set_type(_type)

    def restart(self, pos):
        self.parts = []
        self.add_part(pos)

    def add_part(self, position):
        self.parts.append(SnakePart(position))
        self.update_parttype()

    def grow(self, direction):
        self.move(direction, True)

    def move(self, direction, should_grow=False):
        tail = head = SnakePart(self.get_head().position)

        if not should_grow:
            tail = self.parts.pop(0)

        tail.position = Position(head.position.x, head.position.y)
        if direction == DIRECTION.Left:
            tail.position.x = head.position.x - 1

        if direction == DIRECTION.Right:
            tail.position.x = head.position.x + 1

        if direction == DIRECTION.Up:
            tail.position.y = head.position.y - 1

        if direction == DIRECTION.Down:
            tail.position.y = head.position.y + 1

        self.add_part(tail.position)

    def draw(self, screen):
        for part in self.parts:
            part.draw(screen)

    def erase(self, screen):
        for part in self.parts:
            part.erase(screen)

    def get_head(self):
        return self.parts[self.len()-1]

    def check_food(self, food):
        head = self.get_head()
        return head.hit_test(food.position)

    def check_bite(self, rect):
        head = self.get_head()
        for part in self.parts:
            if part != head and part.hit_test(head.position):
                return True

        head = self.get_head()

        if head.position.x <= rect.x_1:
            return True

        if head.position.x >= rect.x_2:
            return True

        if head.position.y <= rect.y_1:
            return True

        if head.position.y >= rect.y_2:
            return True

        return False

    def __init__(self, start_position):
        self.parts = []
        self.restart(start_position)


class GameScreen:
    handle = None
    play_area = None

    class Rect:
        x_1 = 0
        x_2 = 0
        y_1 = 0
        y_2 = 0

        def __init__(self, x_1, x_2, y_1, y_2):
            self.x_1 = x_1
            self.x_2 = x_2
            self.y_1 = y_1
            self.y_2 = y_2

        def width(self):
            return self.x_2-self.x_1

        def height(self):
            return self.y_2-self.y_1

    def get_handle(self):
        return self.handle

    def check_input(self):
        return self.handle.getch()

    def draw_playarea(self):
        rectangle(self.handle, self.play_area.y_1, self.play_area.x_1,
                  self.play_area.y_2, self.play_area.x_2)

    def clear(self):
        self.handle.clear()

    def random_position(self):
        return Position(random.randrange(self.play_area.x_1+2, self.play_area.x_2-2),
                        random.randrange(self.play_area.y_1+2, self.play_area.y_2-2))

    def reset_screen(self):
        self.handle.nodelay(0)
        self.handle.addstr(self.play_area.y_1 + self.play_area.height() //
                           2, self.play_area.width() // 2 - 5, 'GAME OVER', curses.A_BLINK)
        self.refresh()

    def refresh(self):
        self.handle.refresh()

    def __init__(self, handle):
        self.handle = handle

        self.handle.nodelay(1)
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

        self.play_area = self.Rect(x_1=0, x_2=handle.getmaxyx()[
            1]-1, y_1=4, y_2=handle.getmaxyx()[0]-2)


class SnakeGame:
    screen = None
    lives = 4
    speed = 5
    food = None
    score = 0
    direction = None
    start_time = 0
    elapsed_time = 0
    snake = None

    def __init__(self, handle):
        self.screen = GameScreen(handle)
        self.start_time = time.time()
        self.snake = Snake(self.screen.random_position())
        self.reset_round()

    def reset_round(self):
        self.place_food()
        self.direction = None
        self.snake.restart(self.screen.random_position())
        self.place_food()

    def place_food(self):
        self.food = SnakeFood(self.screen.random_position())

    def draw_console(self):
        msg = '  -> Welcome to the game of Snake <-  '
        self.screen.get_handle().addstr(1, self.screen.play_area.width()//2-len(msg)//2,
                                        msg, curses.color_pair(3))
        msg = r' Lives: %s    Speed: %2d    Score: %d    Time: %02d:%02d ' % (
            chr(182) * self.lives, self.speed, self.score,
            self.elapsed_time/60, self.elapsed_time % 60)

        self.screen.get_handle().addstr(3, self.screen.play_area.width()//2-len(msg)//2,
                                        msg, curses.color_pair(1))

    def draw_game(self):
        self.screen.clear()
        self.screen.draw_playarea()
        self.draw_console()

        self.food.draw(self.screen.get_handle())
        self.snake.draw(self.screen.get_handle())
        self.screen.refresh()

    def check_food(self):
        if self.snake.check_food(self.food):
            playsound('eat.mp3', False)
            self.snake.grow(self.direction)
            self.score += (self.speed + self.snake.len())*5
            self.place_food()

    def process_input(self):
        key = self.screen.check_input()

        if key != -1:
            if key == curses.KEY_LEFT:
                self.direction = DIRECTION.Left
            elif key == curses.KEY_RIGHT:
                self.direction = DIRECTION.Right
            elif key == curses.KEY_UP:
                self.direction = DIRECTION.Up
            elif key == curses.KEY_DOWN:
                self.direction = DIRECTION.Down
            elif key == curses.ascii.ESC:
                return False
            elif chr(key) == '+':
                self.speed = min(self.speed+1, 100)
            elif chr(key) == 'g':
                # For testing
                self.snake.grow(self.direction)
            elif chr(key) == '-':
                self.speed = max(self.speed-1, 1)
        return True

    def game_over(self):
        self.draw_game()
        self.screen.reset_screen()
        self.food.erase(self.screen.get_handle())
        self.snake.erase(self.screen.get_handle())
        playsound('gameover.mp3', False)
        self.screen.check_input()

    def check_death(self):
        if self.snake.check_bite(self.screen.play_area):
            self.reset_round()
            self.lives -= 1
            if self.lives < 1:
                self.game_over()
                return True

            playsound('round.mp3', False)
        return False

    def play(self):
        while True:
            self.elapsed_time = time.time() - self.start_time

            if not self.process_input():
                return

            self.snake.move(self.direction)
            self.draw_game()
            self.check_food()

            if self.check_death():
                return

            time.sleep(1./self.speed)


def main(stdscr):
    game = SnakeGame(stdscr)
    game.play()


if __name__ == '__main__':

    random.seed(time.time())

    curses.wrapper(main)
    curses.curs_set(1)
