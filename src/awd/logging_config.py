"""Central logging setup for CLI and library use."""

from __future__ import annotations

import logging
import sys


def configure_logging(verbosity: int = 0) -> None:
    """Configure root logging.

    verbosity 0 → WARNING, 1 → INFO, 2+ → DEBUG
    """
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        for handler in root.handlers:
            handler.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%H:%M:%S")
    )
    handler.setLevel(level)
    root.addHandler(handler)
    root.setLevel(level)

    logging.getLogger("awd").setLevel(level)
