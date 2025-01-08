import random
import datetime
import json
import os
from pathlib import Path
from typing import Any


class DailyRandomGenerator:
    """A class that generates and caches daily random numbers."""

    _cache_file: Path
    _daily_cache: tuple[datetime.date, float | None]

    def __init__(self) -> None:
        self._cache_file = Path(os.path.dirname(__file__)) / ".daily_random_cache.json"
        self._daily_cache = self._load_cache()

    def _load_cache(self) -> tuple[datetime.date, float | None]:
        """Load cache from file or return default if no cache exists."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, "r") as f:
                    data: dict[str, Any] = json.load(f)
                    return (datetime.date.fromisoformat(data["date"]), data["value"])
        except (json.JSONDecodeError, KeyError, ValueError):
            # If there's any error reading the cache, return default values
            pass
        return (datetime.date.today(), None)

    def _save_cache(self) -> None:
        """Save current cache to file."""
        data = {"date": self._daily_cache[0].isoformat(), "value": self._daily_cache[1]}
        with open(self._cache_file, "w") as f:
            json.dump(data, f)

    def random_normal_in_range(self, min_val: int, max_val: int) -> float:
        """
        Generate a random number from a truncated normal distribution
        between [min_val, max_val]. A *new* value is returned on each call.
        """
        mean = (min_val + max_val) / 2
        std_dev = (
            max_val - min_val
        ) / 6  # This ensures ~99.7% of values fall within range

        while True:
            value = random.gauss(mean, std_dev)
            if min_val <= value <= max_val:
                return value

    def daily_random_normal_in_range(self, min_val: int, max_val: int) -> float:
        """
        Generate a random number from a truncated normal distribution
        between [min_val, max_val], but only once per calendar day.

        - On the first call *today*, pick a new value and store it.
        - For any subsequent calls on the same day, return the same value.
        """
        today = datetime.date.today()

        if today != self._daily_cache[0] or self._daily_cache[1] is None:
            # Generate new value if date differs or if we have no cached value
            value = self.random_normal_in_range(min_val, max_val)
            self._daily_cache = (today, value)
            self._save_cache()

        assert self._daily_cache[1] is not None
        return self._daily_cache[1]


# Create a singleton instance
_generator = DailyRandomGenerator()


# Provide module-level functions that use the singleton
def random_normal_in_range(min_val: int, max_val: int) -> float:
    return _generator.random_normal_in_range(min_val, max_val)


def daily_random_normal_in_range(min_val: int, max_val: int) -> float:
    return _generator.daily_random_normal_in_range(min_val, max_val)


if __name__ == "__main__":
    # Example usage:
    print("Two different calls in the same run (should differ):")
    val1 = random_normal_in_range(0, 10)
    val2 = random_normal_in_range(0, 10)
    print(f"{val1} {val2}")

    print("\nTwo daily values in the same run (should be the same):")
    daily_val1 = daily_random_normal_in_range(0, 10)
    daily_val2 = daily_random_normal_in_range(0, 10)
    print(f"{daily_val1} {daily_val2}")
