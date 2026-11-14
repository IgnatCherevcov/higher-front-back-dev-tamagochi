"""Логика начисления монет за работу."""

from abc import ABC, abstractmethod
from random import randint


class AbstractClicker(ABC):
    """Контракт кликера."""

    @abstractmethod
    def __init__(self) -> None:
        """Инициализировать кликер."""

    @abstractmethod
    def click(self) -> None:
        """Выполнить действие для заработка."""

    @property
    @abstractmethod
    def income_per_click(self) -> int:
        """Вернуть доход последнего действия."""


class SimpleRandomClicker(AbstractClicker):
    """Кликер со случайным доходом в заданных пределах."""

    def __init__(self, min_income: int = 10, max_income: int = 20) -> None:
        """Задать границы дохода.

        Raises:
            ValueError: Если границы некорректны.
        """
        if min_income < 0 or max_income < min_income:
            raise ValueError('Некорректные границы дохода')
        self.min_income = min_income
        self.max_income = max_income
        self._income_per_click = 0

    @property
    def income_per_click(self) -> int:
        """Вернуть монеты, заработанные последним кликом."""
        return self._income_per_click

    def click(self) -> None:
        """Рассчитать доход от очередного клика."""
        self._income_per_click = randint(self.min_income, self.max_income)
