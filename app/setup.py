"""Utility functions for ensuring application setup."""

import os


def ensure_directory_exists(directory_path: str):
    """Ensure a directory exists"""
    os.makedirs(directory_path, exist_ok=True)


def setup_directories() -> None:
    """Set up all required application directories."""

    ensure_directory_exists("data")
    ensure_directory_exists("log")
    ensure_directory_exists("backups")
