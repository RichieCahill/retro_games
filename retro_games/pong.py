"""A pong game."""

from __future__ import annotations

import curses
import logging
import time
from enum import Enum
from random import choice

from retro_games.game_components import (
    Collidable,
    CollisionError,
    CollisionMap,
    EntityID,
    Game,
    GameEntity,
    Renderer,
)


class PongEntityID(EntityID):
    """A pong entity id."""

    PADDLE = 5
    BALL = 6
    SCORE = 7


class Paddle(GameEntity, Collidable):
    """A paddle."""

    def __init__(self, x: int, game: Pong, height: int = 4, *, ai: bool = False) -> None:
        """Init."""
        super().__init__(game.screen)

        self.height = height
        self.width = 1
        self.ai = ai

        self.x = self.new_x = x
        self.y = self.new_y = (self.max_y - self.height) // 2

        self.entity_id = PongEntityID.PADDLE

        self.update_map(game.collision_map)

    def draw(self) -> None:
        """Draw the paddle on the screen."""
        for i in range(self.height):
            self.screen.addch(self.y + i, self.x, "│")

    def update_map(self, collision_map: CollisionMap) -> None:
        """Update the collision map."""
        for i in range(self.height):
            collision_map.map[self.y + i][self.x] = PongEntityID.EMPTY
        for i in range(self.height):
            collision_map.map[self.new_y + i][self.new_x] = self.entity_id
        self.y = self.new_y

    def ai_move(self, game: Pong) -> None:
        """AI movement logic."""
        if not self.ai:
            return

        distension = abs(game.ball.x - self.x)
        if distension > game.max_x // 12:
            return

        ball_center = game.ball.y
        paddle_center = self.y + (self.height // 2)

        if paddle_center < ball_center:
            self.move(game, Paddle.Direction.DOWN)
        if paddle_center > ball_center:
            self.move(game, Paddle.Direction.UP)

    class Direction(Enum):
        """A paddle direction."""

        UP = -1
        DOWN = 1

    def move(self, game: Pong, direction: Direction) -> None:
        """Move the ball and handle wall collisions."""
        self.new_y = self.y + direction.value

        collision = game.collision_map.check_collision(self)

        if collision in (
            {PongEntityID.EMPTY, PongEntityID.PADDLE},
            {PongEntityID.EMPTY},
            # this allows the paddle to clip the ball
            {PongEntityID.BALL, PongEntityID.PADDLE},
        ):
            self.update_map(game.collision_map)
            return

        if collision in ({PongEntityID.BOTTOM_WALL}, {PongEntityID.TOP_WALL}):
            return

        raise CollisionError(collision)


class Score(GameEntity):
    """A score."""

    def __init__(self, screen: curses.window, x: int, y: int) -> None:
        """Init."""
        super().__init__(screen)
        self.x = x
        self.y = y
        self.player_1_score = 0
        self.player_2_score = 0

    def draw(self) -> None:
        """Draw the score on the screen."""
        self.screen.addstr(self.y, self.x, f"Player 1: {self.player_1_score}")
        self.screen.addstr(self.y, self.x + self.max_x // 4, f"Player 2: {self.player_2_score}")


class Ball(GameEntity, Collidable):
    """A ball."""

    def __init__(self, game: Pong) -> None:
        """Init."""
        super().__init__(game.screen)

        self.width = 1
        self.height = 1

        self.entity_id = PongEntityID.BALL

        self.reset(game)

    def draw(self) -> None:
        """Draw the ball on the screen."""
        self.screen.addch(self.y, self.x, "●")

    def update_map(self, collision_map: CollisionMap) -> None:
        """Update the collision map."""
        collision_map.map[self.y][self.x] = PongEntityID.EMPTY
        self.x = self.new_x
        self.y = self.new_y
        collision_map.map[self.new_y][self.new_x] = self.entity_id

    def reset(self, game: Pong) -> None:
        """Reset ball to center with random direction."""
        self.new_x = self.max_x // 2
        self.new_y = self.max_y // 2

        self.update_map(game.collision_map)

        self.x_direction = choice([-1, 1])  # noqa: S311
        self.y_direction = choice([-1, 1])  # noqa: S311

    def move(self, game: Pong) -> None:
        """Move the ball and handle wall collisions."""
        self.new_x = self.x + self.x_direction
        self.new_y = self.y + self.y_direction

        collision = game.collision_map.check_collision(self)

        if collision == {PongEntityID.EMPTY}:
            self.update_map(game.collision_map)
            return

        if collision in ({PongEntityID.BOTTOM_WALL}, {PongEntityID.TOP_WALL}):
            self.y_direction *= -1
            return

        if collision == {PongEntityID.PADDLE}:
            self.x_direction *= -1
            return

        if collision == {PongEntityID.LEFT_WALL}:
            game.score.player_1_score += 1
            self.reset(game)
            return

        if collision == {PongEntityID.RIGHT_WALL}:
            game.score.player_2_score += 1
            self.reset(game)
            return

        raise CollisionError(collision)


class Pong(Game):
    """A pong game."""

    def __init__(self, screen: curses.window) -> None:
        """Init."""
        self.screen = screen
        self.max_y, self.max_x = screen.getmaxyx()

        super().__init__(self.max_y, self.max_x - 2, PongEntityID())

        logging.info(f"{self.max_y=}, {self.max_x=}")
        logging.info(f"{len(self.collision_map.map)=}")
        logging.info(f"{len(self.collision_map.map[0])=}")

        # Create game entities
        self.left_paddle = Paddle(2, self, ai=True)
        self.right_paddle = Paddle(self.max_x - 1, self, ai=True)
        self.ball = Ball(self)
        self.score = Score(screen, self.max_x // 4, 0)

        self.entities = [self.left_paddle, self.right_paddle, self.ball, self.score]

        self.key_map = {
            ord("w"): (self.left_paddle.move, (self, Paddle.Direction.UP)),
            ord("s"): (self.left_paddle.move, (self, Paddle.Direction.DOWN)),
            ord("q"): (lambda: 1, ()),
        }
        # Create renderer
        self.renderer = Renderer(screen)

        # Initialize screen
        curses.curs_set(0)
        screen.timeout(50)

    def update(self) -> None:
        """Update the game."""
        self.ball.move(self)
        self.right_paddle.ai_move(self)
        self.left_paddle.ai_move(self)

    def run(self) -> None:
        """Run the game."""
        while True:
            if self.handle_input() == 1:
                break

            self.update()

            # Render all entities
            self.renderer.render(self.entities)

            time.sleep(0.05)
