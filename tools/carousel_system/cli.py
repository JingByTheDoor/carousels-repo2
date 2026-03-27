from __future__ import annotations

import sys
from collections.abc import Callable

from carousel_system.config import ConfigError


def run(main: Callable[[], int]) -> int:
    try:
        return main()
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1
