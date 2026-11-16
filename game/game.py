"""Интерфейс игры и управление игровой экономикой."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from copy import copy
from typing import Any

from .clicker import AbstractClicker
from .constants import INITIAL_COINS
from .exceptions import InvalidItemSelection, NotEnoughMoney
from .models import Food, Medicine
from .tamagochi import AbstractTamagochi

ShopItem = Food | Medicine
ItemSelector = Callable[[Sequence[ShopItem], str], ShopItem | None]


class AbstractGame(ABC):
    """Контракт управления игровыми действиями и ресурсами."""

    @abstractmethod
    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine],
    ) -> None:
        """Сохранить игровые компоненты и ассортимент.

        Args:
            tamagochi: Реализация питомца.
            clicker: Компонент заработка.
            all_food: Доступные продукты питания.
            all_medicine: Доступные лекарства.
        """

    @abstractmethod
    def work(self) -> int:
        """Заработать монеты и обновить состояние питомца.

        Returns:
            Количество монет за одно действие.
        """

    @abstractmethod
    def buy_food(self) -> None:
        """Купить одну порцию еды."""

    @abstractmethod
    def buy_medicine(self) -> None:
        """Купить лекарство."""

    @abstractmethod
    def feed_tamagochi(self) -> None:
        """Покормить питомца одной порцией еды."""

    @abstractmethod
    def heal_tamagochi(self) -> None:
        """Применить лекарство к питомцу."""

    @abstractmethod
    def rest_tamagochi(self) -> None:
        """Дать питомцу отдохнуть."""

    @abstractmethod
    def play_with_tamagochi(self) -> None:
        """Поиграть с питомцем."""

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """Получить текущие игровые показатели.

        Returns:
            Словарь с характеристиками и балансом.
        """

    @property
    @abstractmethod
    def food(self) -> list[Food]:
        """Получить список доступной еды.

        Returns:
            Список продуктов в инвентаре.
        """

    @property
    @abstractmethod
    def medicine(self) -> list[Medicine]:
        """Получить список доступных лекарств.

        Returns:
            Список препаратов в инвентаре.
        """


class SimpleGame(AbstractGame):
    """Игровая логика с независимым от неё интерфейсом выбора предметов."""

    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine],
        selector: ItemSelector | None = None,
    ) -> None:
        """Создать игру с компонентами и ассортиментом.

        Args:
            tamagochi: Питомец, соответствующий абстрактному интерфейсу.
            clicker: Кликер для получения монет.
            all_food: Список продуктов магазина.
            all_medicine: Список препаратов магазина.
            selector: Функция выбора предмета без привязки к консоли.
        """
        self._tamagochi = tamagochi
        self._clicker = clicker
        self._all_food = tuple(all_food)
        self._all_medicine = tuple(copy(item) for item in all_medicine)
        self._coins = INITIAL_COINS
        self._food: list[Food] = []
        self._medicine: list[Medicine] = []
        self._selector = selector

    @property
    def tamagochi(self) -> AbstractTamagochi:
        """Вернуть объект питомца для использования его интерфейса.

        Returns:
            Питомец игры.
        """
        return self._tamagochi

    @property
    def coins(self) -> int:
        """Вернуть текущий баланс.

        Returns:
            Количество монет.
        """
        return self._coins

    @property
    def food(self) -> list[Food]:
        """Вернуть список продуктов в инвентаре.

        Returns:
            Список принадлежащих игроку продуктов.
        """
        return self._food

    @property
    def medicine(self) -> list[Medicine]:
        """Вернуть копию списка препаратов и их текущих состояний.

        Returns:
            Копии лекарств в инвентаре.
        """
        return [copy(item) for item in self._medicine]

    def _choose(
        self, items: Sequence[ShopItem], title: str
    ) -> ShopItem | None:
        """Получить допустимый выбор из переданного списка предметов.

        Args:
            items: Доступные предметы.
            title: Описание списка для интерфейса выбора.

        Returns:
            Выбранный объект либо None при отмене или пустом списке.

        Raises:
            InvalidItemSelection: Если выбран отсутствующий предмет.
        """
        if self._selector is None:
            return items[0] if items else None
        selected = self._selector(items, title)
        if selected is not None and not any(
            selected is item for item in items
        ):
            raise InvalidItemSelection('Предмет отсутствует в списке')
        return selected

    def _buy(self, item: ShopItem) -> None:
        """Оплатить товар и обновить состояние питомца.

        Args:
            item: Продукт или препарат из ассортимента.

        Raises:
            NotEnoughMoney: Если монет недостаточно.
            TamagochiIsGone: Если питомец погиб при обновлении.
        """
        if self._coins < item.price:
            raise NotEnoughMoney('Не хватает монет')
        self._coins -= item.price
        if isinstance(item, Food):
            self._food.append(item)
        else:
            self._medicine.append(copy(item))
        self._tamagochi.update()

    def work(self) -> int:
        """Начислить монеты за работу и обновить состояние питомца.

        Returns:
            Сумма заработка за текущий ход.

        Raises:
            TamagochiIsGone: Если питомец погиб при обновлении.
        """
        self._clicker.click()
        earned = self._clicker.income_per_click
        self._coins += earned
        self._tamagochi.update()
        return earned

    def buy_food(self) -> None:
        """Выбрать продукт и купить его при наличии денег."""
        item = self._choose(self._all_food, 'Доступная еда:')
        if item is not None:
            self._buy(item)

    def buy_medicine(self) -> None:
        """Выбрать препарат и купить его при наличии денег."""
        item = self._choose(self._all_medicine, 'Доступные лекарства:')
        if item is not None:
            self._buy(item)

    def feed_tamagochi(self) -> None:
        """Накормить питомца и израсходовать порцию еды."""
        item = self._choose(self._food, 'Еда в сумке:')
        if item is not None:
            self._tamagochi.feed(item)
            for index, stored in enumerate(self._food):
                if stored is item:
                    del self._food[index]
                    break
            self._tamagochi.update()

    def heal_tamagochi(self) -> None:
        """Вылечить питомца и удалить полностью израсходованный препарат."""
        item = self._choose(self._medicine, 'Лекарства в сумке:')
        if item is not None:
            self._tamagochi.heal(item)
            if item.is_empty():
                self._medicine.remove(item)
            self._tamagochi.update()

    def rest_tamagochi(self) -> None:
        """Восстановить силы питомца и применить изменения за ход."""
        self._tamagochi.rest()
        self._tamagochi.update()

    def play_with_tamagochi(self) -> None:
        """Поиграть с питомцем и применить изменения за ход."""
        self._tamagochi.play()
        self._tamagochi.update()

    def get_status(self) -> dict[str, Any]:
        """Получить состояние питомца и баланс монет.

        Returns:
            Независимый словарь со всеми игровыми показателями.
        """
        return {**self._tamagochi.status, 'coins': self._coins}
