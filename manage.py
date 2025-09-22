#!/usr/bin/env python
"""Thin wrapper delegating to backend.manage for backwards compatibility."""
from backend.manage import main

if __name__ == "__main__":
    main()
