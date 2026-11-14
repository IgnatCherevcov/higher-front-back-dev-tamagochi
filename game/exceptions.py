"""Исключения игровых действий."""


class TamagochiIsGone(Exception):
    """Здоровье питомца опустилось ниже нуля."""


class NotEnoughMoney(Exception):
    """Недостаточно монет для покупки."""
