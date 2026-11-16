"""Исключения, возникающие в игровых ситуациях."""


class GameError(Exception):
    """Базовая ошибка игрового действия."""


class TamagochiIsGone(GameError):
    """Питомец погиб, продолжение игры невозможно."""


class NotEnoughMoney(GameError):
    """Недостаточно монет для покупки."""


class NotEnoughEnergy(GameError):
    """Питомцу не хватает энергии для игры."""


class MedicineIsEmpty(GameError):
    """У лекарства не осталось применений."""


class InvalidItemSelection(GameError):
    """Выбран предмет, отсутствующий в доступном списке."""
