"""Explicit interactive-desktop opt-in for real acceptance runs."""

import pytest


def pytest_addoption(parser):
    parser.addoption("--allow-desktop-input", action="store_true", default=False)


def pytest_collection_modifyitems(config, items):
    if any("integration" in item.keywords for item in items):
        if not config.getoption("--allow-desktop-input"):
            raise pytest.UsageError("Real HPE990 BDD requires --allow-desktop-input")


def pytest_bdd_apply_tag(tag, function):
    if tag.startswith(("ISSUE-", "AC-")):
        return True
