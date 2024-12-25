"""Game components."""

from __future__ import annotations

import curses
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import curses
    from collections.abc import Callable


class CollisionMap:
    """A collision map."""

    class MapEntity(Enum):
        """A map entity."""

        EMPTY = 0
        PADDLE = 1
        BALL = 2
        BOARDER = 3
        TOP_WALL = 4
        BOTTOM_WALL = 5
        LEFT_WALL = 6
        RIGHT_WALL = 7

    map: list[list[MapEntity]]

    def __init__(self, max_y: int, max_x: int) -> None:
        """Init."""
        self.max_y = max_y
        self.max_x = max_x

        self.map = self.create_collision_map()

        logging.info(f"{self.max_y=}, {self.max_x=}")
        logging.info(f"{len(self.map)=}")
        logging.info(f"{len(self.map[0])=}")

    def create_collision_map(self) -> list[list[MapEntity]]:
        """Create a collision map for the game.

        Returns:
            A list of lists representing the collision map.
        """
        return [[self.MapEntity.EMPTY for _ in range(self.max_x)] for _ in range(self.max_y)]

    def check_collision(self, entity: Collidable) -> set[MapEntity]:
        """Check if the object collides with the collision map."""
        if entity.new_x < 0 + 1:
            return {self.MapEntity.LEFT_WALL}
        if entity.new_x >= self.max_x + 1 - entity.width:
            return {self.MapEntity.RIGHT_WALL}
        if entity.new_y < 0 + 1:
            return {self.MapEntity.TOP_WALL}
        if entity.new_y >= self.max_y - entity.height:
            return {self.MapEntity.BOTTOM_WALL}
        all_collisions: set[CollisionMap.MapEntity] = set()
        for i in range(entity.height):
            part = self.map[entity.new_y + i][entity.new_x : entity.new_x + entity.width]
            all_collisions.update(part)
        return all_collisions


class Collidable(ABC):
    """A collidable object."""

    x: int
    y: int
    width: int
    height: int
    new_x: int
    new_y: int
    map_entity_type: CollisionMap.MapEntity

    @abstractmethod
    def update_map(self, collision_map: CollisionMap) -> None:
        """Update the collision map."""


class GameEntity(ABC):
    """A game entity."""

    def __init__(self, screen: curses.window) -> None:
        """Init."""
        """Initialize the entity."""
        self.screen = screen
        self.max_y, self.max_x = screen.getmaxyx()
        self.x = 0
        self.y = 0

    @abstractmethod
    def draw(self) -> None:
        """Draw the entity on the screen."""


class Game:
    """A game."""

    screen: curses.window
    key_map: dict[int, tuple[Callable, tuple]]
    entities: list[GameEntity]
    collision_map: CollisionMap

    def __init__(self, max_y: int, max_x: int) -> None:
        """Init."""
        self.max_y = max_y
        self.max_x = max_x

        self.collision_map = CollisionMap(max_y, max_x)

    def handle_input(self) -> bool:
        """Handle input."""
        key = self.screen.getch()

        func, args = self.key_map.get(key, (lambda: None, ()))
        if args:
            return func(*args)

        return func()


class Renderer:
    """A game renderer."""

    def __init__(self, screen: curses.window) -> None:
        """Init."""
        self.screen = screen

    def render(self, entities: list[GameEntity]) -> None:
        """Render the entities on the screen."""
        self.screen.clear()
        self.screen.border()

        for entity in entities:
            entity.draw()

        self.screen.refresh()
