"""Неофициальная асинхронная библиотека для работы с API школьного дневника МЭШ."""

from .client import MOSDiaryClient

__version__ = "0.2.0"

__all__ = ("MOSDiaryClient", "__version__")