"""Shared extension instances.

Kept in their own module so models and the app factory can both import them
without creating circular references.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
