"""A simple pong game using curses."""

from __future__ import annotations

import curses
import logging

from retro_games.pong import Pong


def configure_logger(level: str = "INFO") -> None:
    """Configure the logger.

    Args:
        level (str, optional): The logging level. Defaults to "INFO".
    """
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s",
        handlers=[logging.FileHandler("retro_games.log")],
    )


def main() -> None:
    """Main."""
    configure_logger(level="DEBUG")
    try:
        stdscr = curses.initscr()
        game = Pong(stdscr)
        game.run()
    except Exception:
        logging.exception("Found an error")


if __name__ == "__main__":
    main()
