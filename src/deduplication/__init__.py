"""Deduplication module using domain matching, exact canonical name matching, and RapidFuzz similarity."""

from src.deduplication.resolver import DeduplicationResolver

__all__ = ["DeduplicationResolver"]
