# db/__init__.py
from .master_db import get_master_db, get_database

__all__ = ['get_master_db', 'get_database']