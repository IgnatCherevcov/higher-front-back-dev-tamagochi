"""Контракт кликера и реализация случайного заработка."""

from abc import ABC, abstractmethod
from random import randint

from .constants import MAX_CLICK_INCOME, MIN_CLICK_INCOME


class AbstractClicker(ABC):
    """Интерфейс компонента заработка монет."""

    @abstractmethod
    def __init__(self) -> None:
        """Инициализировать компонент заработка."""

    @abstractmethod
    def click(self) -> None:
        """Рассчитать доход от одного действия."""

    @property
    @abstractmethod
    def income_per_click(self) -> int:
        """Вернуть доход от последнего действия.

        Returns:
            Количество монет.
        """


class SimpleRandomClicker(AbstractClicker):
    """Кликер со случайным доходом в заданных пределах."""

    def __init__(
        self,
        min_income: int = MIN_CLICK_INCOME,
        max_income: int = MAX_CLICK_INCOME,
    ) -> None:
        """Установить границы дохода.

        Args:
            min_income: Наименьший возможный доход.
            max_income: Наибольший возможный доход.

        Raises:
            ValueError: Если границы дохода некорректны.
        """
        if min_income < 0 or max_income < min_income:
            raise ValueError('Некорректные границы дохода')
        self._min_income = min_income
        self._max_income = max_income
        self._income_per_click = 0

    @property
    def income_per_click(self) -> int:
        """Вернуть доход от последнего клика.

        Returns:
            Количество заработанных монет.
        """
        return self._income_per_click

    def click(self) -> None:
        """Обновить величину дохода с помощью генератора случайных чисел."""
        self._income_per_click = randint(
            self._min_income, self._max_income
        )
