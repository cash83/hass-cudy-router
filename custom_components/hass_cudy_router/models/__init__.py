"""
Model package entrypoint.

IMPORTANT:
This module must be import-safe.

It must NOT import individual model packages (wr6500, r700, etc.),
because unfinished models would crash imports when Home Assistant
or smoke tests import the integration package.

All model registration is handled in registry.py.
"""

from __future__ import annotations

from .registry import create_model_integration

__all__ = ["create_model_integration"]