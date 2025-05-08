#!/usr/bin/env python3
"""Configuration file for Discord invite bot."""

# File paths
TOKEN_FILE = "token"

# Load token from file at import time
with open(TOKEN_FILE) as f:
    TOKEN = f.read().strip()
