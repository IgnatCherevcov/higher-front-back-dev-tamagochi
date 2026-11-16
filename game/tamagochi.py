"""Контракт питомца и реализация изменения его характеристик."""

from abc import ABC, abstractmethod
from random import random

from .constants import (
    DEFAULT_PET_NAME,
    EXHAUSTION_DAMAGE,
    FATIGUE_DAMAGE_THRESHOLD,
    FEED_ENERGY_COST,
    HUNGER_DAMAGE,
    HUNGER_DAMAGE_THRESHOLD,
    INITIAL_ENERGY,
    INITIAL_FATIGUE,
    INITIAL_HP,
    INITIAL_HUNGER,
    MAX_STAT_VALUE,
    MIN_STAT_VALUE,
    PLAY_ENERGY_COST,
    PLAY_FATIGUE_GAIN,
    PLAY_HUNGER_GAIN,
    REST_RECOVERY,
    SICK_REST_RECOVERY,
    SICKNESS_DAMAGE,
    SICKNESS_PROBABILITY,
    TICK_ENERGY_COST,
    TICK_FATIGUE_GAIN,
    TICK_HUNGER_GAIN,
)
from .exceptions import NotEnoughEnergy, TamagochiIsGone
from .models import Food, Medicine


class AbstractTamagochi(ABC):
    """Интерфейс управления состоянием питомца."""

    @abstractmethod
    def feed(self, food: Food) -> None:
        """Накормить питомца.

        Args:
            food: Продукт питания.
        """

    @abstractmethod
    def play(self) -> None:
        """Поиграть с питомцем."""

    @abstractmethod
    def rest(self) -> None:
        """Дать питомцу отдохнуть."""

    @abstractmethod
    def heal(self, medicine: Medicine) -> None:
        """Применить лекарство к питомцу.

        Args:
            medicine: Используемый препарат.
        """

    @property
    @abstractmethod
    def status(self) -> dict[str, int]:
        """Вернуть текущие показатели питомца.

        Returns:
            Независимый словарь с характеристиками.
        """

    @abstractmethod
    def is_alive(self) -> bool:
        """Проверить, жив ли питомец.

        Returns:
            True, если уровень здоровья не ниже нуля.
        """

    @abstractmethod
    def is_sick(self) -> bool:
        """Проверить, болен ли питомец.

        Returns:
            True, если питомец болен.
        """

    @abstractmethod
    def update(self) -> None:
        """Применить изменения характеристик за один игровой ход."""


class SimpleTamagochi(AbstractTamagochi):
    """Питомец с голодом, усталостью, здоровьем и энергией."""

    def __init__(self, name: str = DEFAULT_PET_NAME) -> None:
        """Установить имя и начальное состояние питомца.

        Args:
            name: Имя питомца.
        """
        self._name = name
        self._hunger = INITIAL_HUNGER
        self._fatigue = INITIAL_FATIGUE
        self._hp = INITIAL_HP
        self._energy = INITIAL_ENERGY
        self._sick = False

    @property
    def name(self) -> str:
        """Вернуть имя питомца.

        Returns:
            Строка с именем.
        """
        return self._name

    @property
    def status(self) -> dict[str, int]:
        """Вернуть копию текущего состояния.

        Returns:
            Характеристики питомца в виде словаря.
        """
        return {
            'hunger': self._hunger,
            'fatigue': self._fatigue,
            'hp': self._hp,
            'energy': self._energy,
        }

    def is_alive(self) -> bool:
        """Проверить, не погиб ли питомец.

        Returns:
            True при здоровье от нуля и выше.
        """
        return self._hp >= MIN_STAT_VALUE

    def is_sick(self) -> bool:
        """Получить признак болезни.

        Returns:
            True при наличии болезни.
        """
        return self._sick

    def _check_alive(self) -> None:
        """Запретить действия после гибели питомца.

        Raises:
            TamagochiIsGone: Если уровень здоровья ниже нуля.
        """
        if not self.is_alive():
            raise TamagochiIsGone('Питомец погиб')

    def feed(self, food: Food) -> None:
        """Уменьшить голод и затратить энергию на кормление.

        Args:
            food: Используемый продукт питания.

        Raises:
            TamagochiIsGone: Если питомец погиб.
        """
        self._check_alive()
        self._hunger = max(MIN_STAT_VALUE, self._hunger - food.satiety)
        self._energy = max(MIN_STAT_VALUE, self._energy - FEED_ENERGY_COST)

    def play(self) -> None:
        """Израсходовать энергию и повысить усталость и голод.

        Raises:
            NotEnoughEnergy: Если энергии недостаточно.
            TamagochiIsGone: Если питомец погиб.
        """
        self._check_alive()
        if self._energy < PLAY_ENERGY_COST:
            raise NotEnoughEnergy('Недостаточно энергии для игры')
        self._energy -= PLAY_ENERGY_COST
        self._fatigue = min(MAX_STAT_VALUE, self._fatigue + PLAY_FATIGUE_GAIN)
        self._hunger = min(MAX_STAT_VALUE, self._hunger + PLAY_HUNGER_GAIN)

    def rest(self) -> None:
        """Восстановить энергию и снизить усталость.

        Raises:
            TamagochiIsGone: Если питомец погиб.
        """
        self._check_alive()
        recovery = SICK_REST_RECOVERY if self._sick else REST_RECOVERY
        self._energy = min(MAX_STAT_VALUE, self._energy + recovery)
        self._fatigue = max(MIN_STAT_VALUE, self._fatigue - recovery)

    def heal(self, medicine: Medicine) -> None:
        """Вылечить питомца, использовав одну дозу препарата.

        Args:
            medicine: Препарат для лечения.

        Raises:
            MedicineIsEmpty: Если препарат израсходован.
            TamagochiIsGone: Если питомец погиб.
        """
        self._check_alive()
        medicine.use()
        self._hp = min(MAX_STAT_VALUE, self._hp + medicine.heal_hp)
        self._sick = False

    def update(self) -> None:
        """Изменить характеристики, применить болезни и урон за ход.

        Raises:
            TamagochiIsGone: Если питомец погиб.
        """
        self._check_alive()
        self._hunger = min(MAX_STAT_VALUE, self._hunger + TICK_HUNGER_GAIN)
        self._fatigue = min(
            MAX_STAT_VALUE, self._fatigue + TICK_FATIGUE_GAIN
        )
        self._energy = max(MIN_STAT_VALUE, self._energy - TICK_ENERGY_COST)
        if not self._sick and random() < SICKNESS_PROBABILITY:
            self._sick = True
        damage = SICKNESS_DAMAGE if self._sick else MIN_STAT_VALUE
        if self._hunger >= HUNGER_DAMAGE_THRESHOLD:
            damage += HUNGER_DAMAGE
        if (
            self._fatigue >= FATIGUE_DAMAGE_THRESHOLD
            or self._energy == MIN_STAT_VALUE
        ):
            damage += EXHAUSTION_DAMAGE
        self._hp -= damage
        self._check_alive()
