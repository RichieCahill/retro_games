"""A pong game."""

from __future__ import annotations

import curses
import logging
import time
from enum import Enum
from random import choice

from retro_games.game_components import Collidable, CollisionMap, Game, GameEntity, Renderer


class Paddle(GameEntity, Collidable):
    """A paddle."""

    def __init__(self, x: int, screen: curses.window, height: int = 4) -> None:
        """Init."""
        super().__init__(screen)
        self.x = x
        self.new_x = x
        self.height = height
        self.width = 1
        self.y = (self.max_y - self.height) // 2
        self.map_entity_type = CollisionMap.MapEntity.PADDLE

    def draw(self) -> None:
        """Draw the paddle on the screen."""
        for i in range(self.height):
            self.screen.addch(self.y + i, self.x, "│")

    def update_map(self, collision_map: CollisionMap) -> None:
        """Update the collision map."""
        for i in range(self.height):
            collision_map.map[self.y + i][self.x] = collision_map.MapEntity.EMPTY
        for i in range(self.height):
            collision_map.map[self.new_y + i][self.new_x] = self.map_entity_type
        self.y = self.new_y

    class Direction(Enum):
        """A paddle direction."""

        UP = -1
        DOWN = 1

    def move(self, collision_map: CollisionMap, direction: Direction) -> None:
        """Move the ball and handle wall collisions."""
        self.new_y = self.y + direction.value

        collision = collision_map.check_collision(self)

        if collision in (
            {collision_map.MapEntity.EMPTY, collision_map.MapEntity.PADDLE},
            {collision_map.MapEntity.EMPTY},
        ):
            self.update_map(collision_map)
            return

        if collision in ({collision_map.MapEntity.BOTTOM_WALL}, {collision_map.MapEntity.TOP_WALL}):
            return

        error = f"Unexpected collision: {collision}"
        raise ValueError(error)


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

    def __init__(self, screen: curses.window) -> None:
        """Init."""
        super().__init__(screen)
        self.reset()

    def draw(self) -> None:
        """Draw the ball on the screen."""
        self.screen.addch(self.y, self.x, "●")

    def update_map(self, collision_map: CollisionMap) -> None:
        """Update the collision map."""
        collision_map.map[self.y][self.x] = collision_map.MapEntity.EMPTY
        self.x = self.new_x
        self.y = self.new_y
        collision_map.map[self.new_y][self.new_x] = self.map_entity_type

    def reset(self) -> None:
        """Reset ball to center with random direction."""
        self.x = self.max_x // 2
        self.y = self.max_y // 2

        self.width = 1
        self.height = 1

        self.dx = choice([-1, 1])  # noqa: S311
        self.dy = choice([-1, 1])  # noqa: S311

        self.map_entity_type = CollisionMap.MapEntity.BALL

    def move(self, collision_map: CollisionMap, score: Score) -> tuple[CollisionMap, Score]:
        """Move the ball and handle wall collisions."""
        self.new_x = self.x + self.dx
        self.new_y = self.y + self.dy

        collision = collision_map.check_collision(self)

        if collision == {collision_map.MapEntity.EMPTY}:
            self.update_map(collision_map)
            return collision_map, score

        if collision in ({collision_map.MapEntity.BOTTOM_WALL}, {collision_map.MapEntity.TOP_WALL}):
            self.dy *= -1
            return collision_map, score

        if collision == {collision_map.MapEntity.PADDLE}:
            self.dx *= -1

            return collision_map, score

        if collision == {collision_map.MapEntity.LEFT_WALL}:
            score.player_1_score += 1
            collision_map.map[self.y][self.x] = collision_map.MapEntity.EMPTY
            self.reset()
            return collision_map, score

        if collision == {collision_map.MapEntity.RIGHT_WALL}:
            score.player_2_score += 1
            collision_map.map[self.y][self.x] = collision_map.MapEntity.EMPTY
            self.reset()
            return collision_map, score

        error = f"Unexpected collision: {collision}"
        raise ValueError(error)

    def check_scoring(self) -> tuple[int, int]:
        """Check if ball has passed paddles and return scoring info."""
        if self.x <= 0:
            self.reset()
            return 0, 1
        if self.x >= self.max_x - 1:
            self.reset()
            return 1, 0
        return 0, 0


class Pong(Game):
    """A pong game."""

    def __init__(self, screen: curses.window) -> None:
        """Init."""
        self.screen = screen
        self.max_y, self.max_x = screen.getmaxyx()

        super().__init__(self.max_y, self.max_x - 2)

        logging.info(f"{self.max_y=}, {self.max_x=}")
        logging.info(f"{len(self.collision_map.map)=}")
        logging.info(f"{len(self.collision_map.map[0])=}")

        # Create game entities
        self.left_paddle = Paddle(2, screen)
        self.right_paddle = Paddle(self.max_x - 2, screen)
        self.ball = Ball(screen)
        self.score = Score(screen, self.max_x // 4, 0)

        self.entities = [self.left_paddle, self.right_paddle, self.ball, self.score]

        self.key_map = {
            ord("w"): (self.left_paddle.move, (self.collision_map, Paddle.Direction.UP)),
            ord("s"): (self.left_paddle.move, (self.collision_map, Paddle.Direction.DOWN)),
            ord("i"): (self.right_paddle.move, (self.collision_map, Paddle.Direction.UP)),
            ord("k"): (self.right_paddle.move, (self.collision_map, Paddle.Direction.DOWN)),
            ord("q"): (lambda: 1, ()),
        }
        # Create renderer
        self.renderer = Renderer(screen)

        # Initialize screen
        curses.curs_set(0)
        screen.timeout(50)

    def update(self) -> None:
        """Update the game."""
        # Update ball
        self.collision_map, self.score = self.ball.move(self.collision_map, self.score)

    def run(self) -> None:
        """Run the game."""
        while True:
            if self.handle_input() == 1:
                break

            self.update()

            # Render all entities
            self.renderer.render(self.entities)

            time.sleep(0.05)
