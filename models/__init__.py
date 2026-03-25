"""
Модели данных для системы бронирования ресторана.
"""

from .client import ClientModel
from .table import TableModel
from .booking import BookingModel

__all__ = ['ClientModel', 'TableModel', 'BookingModel']
