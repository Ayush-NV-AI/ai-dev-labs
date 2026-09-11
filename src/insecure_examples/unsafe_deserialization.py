"""Training material — deliberately insecure.

Seeded example for the unsafe-deserialization rule.
"""

import pickle

import yaml


def load_cached_report(path: str):
    """Load a previously pickled report object from disk."""
    with open(path, "rb") as f:
        return pickle.load(f)


def load_resource_overrides(raw_yaml: str) -> dict:
    """Parse a resource-overrides config file supplied by an operator."""
    return yaml.load(raw_yaml)
