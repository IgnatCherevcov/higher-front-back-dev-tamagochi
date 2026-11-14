"""Состояние питомца и действия с ним."""

from abc import ABC, abstractmethod
from random import random

from .exceptions import TamagochiIsGone
from .models import Food, Medicine


class AbstractTamagochi(ABC):
    """Контракт управления питомцем."""

    @abstractmethod
    def feed(self, food: Food) -> None:
        """Накормить питомца."""

    @abstractmethod
    def play(self) -> None:
        """Поиграть с питомцем."""

    @abstractmethod
    def rest(self) -> None:
        """Дать питомцу отдохнуть."""

    @abstractmethod
    def heal(self, medicine: Medicine) -> None:
        """Применить лекарство."""

    @property
    @abstractmethod
    def status(self) -> dict[str, int]:
        """Вернуть текущие показатели питомца."""

    @abstractmethod
    def is_alive(self) -> bool:
        """Проверить, жив ли питомец."""

    @abstractmethod
    def is_sick(self) -> bool:
        """Проверить состояние болезни."""

    @abstractmethod
    def update(self) -> None:
        """Обновить потребности питомца за один ход."""


class SimpleTamagochi(AbstractTamagochi):
    """Питомец с голодом, усталостью, здоровьем и энергией."""

    def __init__(self, name: str = 'Пиксель') -> None:
        """Создать питомца с начальными показателями."""
        self.name = name
        self.hunger = 0
        self.fatigue = 0
        self.hp = 100
        self.energy = 100
        self._sick = False

    @property
    def status(self) -> dict[str, int]:
        """Вернуть независимую копию характеристик питомца."""
        return {
            'hunger': self.hunger,
            'fatigue': self.fatigue,
            'hp': self.hp,
            'energy': self.energy,
        }

    def is_alive(self) -> bool:
        """Вернуть False после падения здоровья ниже нуля."""
        return self.hp >= 0

    def is_sick(self) -> bool:
        """Вернуть признак болезни."""
        return self._sick

    def _check_alive(self) -> None:
        """Прервать действия, если питомец погиб.

        Raises:
            TamagochiIsGone: Если питомец погиб.
        """
        if not self.is_alive():
            raise TamagochiIsGone('Питомец погиб')

    def feed(self, food: Food) -> None:
        """Уменьшить голод на величину насыщения еды."""
        self._check_alive()
        self.hunger = max(0, self.hunger - food.satiety)
        self.energy = max(0, self.energy - 2)

    def play(self) -> None:
        """Улучшить настроение ценой энергии и голода."""
        self._check_alive()
        if self.energy < 10:
            raise ValueError('Недостаточно энергии для игры')
        self.energy -= 10
        self.fatigue = min(100, self.fatigue + 7)
        self.hunger = min(100, self.hunger + 5)

    def rest(self) -> None:
        """Восстановить энергию и снизить усталость."""
        self._check_alive()
        recovery = 12 if self._sick else 25
        self.energy = min(100, self.energy + recovery)
        self.fatigue = max(0, self.fatigue - recovery)

    def heal(self, medicine: Medicine) -> None:
        """Восстановить здоровье, расходуя применение лекарства.

        Raises:
            ValueError: Если лекарство закончилось.
        """
        self._check_alive()
        if medicine.is_empty():
            raise ValueError('Лекарство закончилось')
        medicine.uses += 1
        self.hp = min(100, self.hp + medicine.heal_hp)
        self._sick = False

    def update(self) -> None:
        """Обновить потребности, проверить болезнь и гибель.

        Raises:
            TamagochiIsGone: Если здоровье стало ниже нуля.
        """
        self._check_alive()
        self.hunger = min(100, self.hunger + 6)
        self.fatigue = min(100, self.fatigue + 4)
        self.energy = max(0, self.energy - 4)
        if not self._sick and random() < 0.04:
            self._sick = True
        damage = 4 if self._sick else 0
        if self.hunger >= 80:
            damage += 5
        if self.fatigue >= 85 or self.energy == 0:
            damage += 4
        self.hp -= damage
        self._check_alive()
