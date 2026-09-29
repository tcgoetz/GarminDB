"""Progress for the main GarminDB operations."""

import sys

from tqdm import tqdm


def progress(items, label, unit, simple_output=False):
    """Yield items with a progress bar or flushed start and traversal-completion lines."""
    if not simple_output:
        yield from tqdm(items, unit=unit)
        return

    print(label, file=sys.stderr, flush=True)
    visited = 0
    for item in items:
        yield item
        visited += 1
    # Reached only after exhaustion, not after an exception or an early close.
    if visited == 1:
        unit = {'files': 'file', 'days': 'day', 'activities': 'activity', 'weeks': 'week', 'months': 'month'}.get(unit, unit)
    print(f'{label}: {visited} {unit} visited', file=sys.stderr, flush=True)
