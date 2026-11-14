"""Организация игровой экономики и действий игрока."""

from abc import ABC, abstractmethod
from typing import Any

from .clicker import AbstractClicker
from .exceptions import NotEnoughMoney
from .models import Food, Medicine
from .tamagochi import AbstractTamagochi


class AbstractGame(ABC):
    """Контракт игровой логики."""

    @abstractmethod
    def __init__(
        self, tamagochi: AbstractTamagochi, clicker: AbstractClicker,
        all_food: list[Food], all_medicine: list[Medicine]
    ) -> None:
        """Инициализировать игру."""

    @abstractmethod
    def work(self) -> int:
        """Вернуть заработанные монеты."""

    @abstractmethod
    def buy_food(self) -> None:
        """Купить еду."""

    @abstractmethod
    def buy_medicine(self) -> None:
        """Купить лекарство."""

    @abstractmethod
    def feed_tamagochi(self) -> None:
        """Накормить питомца."""

    @abstractmethod
    def heal_tamagochi(self) -> None:
        """Вылечить питомца."""

    @abstractmethod
    def rest_tamagochi(self) -> None:
        """Дать питомцу отдохнуть."""

    @abstractmethod
    def play_with_tamagochi(self) -> None:
        """Поиграть с питомцем."""

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """Вернуть показатели игры."""

    @property
    @abstractmethod
    def food(self) -> list[Food]:
        """Вернуть купленную еду."""

    @property
    @abstractmethod
    def medicine(self) -> list[Medicine]:
        """Вернуть купленные лекарства."""


class SimpleGame(AbstractGame):
    """Консольная игровая логика с магазином и инвентарём."""

    def __init__(
        self, tamagochi: AbstractTamagochi, clicker: AbstractClicker,
        all_food: list[Food], all_medicine: list[Medicine]
    ) -> None:
        """Сохранить игровые компоненты, товары и начальный баланс."""
        self.tamagochi = tamagochi
        self.clicker = clicker
        self.all_food = list(all_food)
        self.all_medicine = list(all_medicine)
        self.coins = 0
        self._food: list[Food] = []
        self._medicine: list[Medicine] = []

    @property
    def food(self) -> list[Food]:
        """Вернуть список еды из инвентаря."""
        return self._food

    @property
    def medicine(self) -> list[Medicine]:
        """Вернуть список лекарств из инвентаря."""
        return self._medicine

    def work(self) -> int:
        """Начислить монеты за работу и вернуть доход."""
        self.clicker.click()
        earned = self.clicker.income_per_click
        self.coins += earned
        return earned

    def _choose(self, items: list[Any], title: str) -> Any | None:
        """Выбрать элемент списка через консоль или вернуть None."""
        if not items:
            print('Список пуст')
            return None
        print(title)
        for index, item in enumerate(items, start=1):
            print(f'{index}. {item}')
        answer = input('Номер (0 — отмена): ').strip()
        if not answer.isdecimal():
            print('Нужно ввести номер')
            return None
        number = int(answer)
        if number == 0:
            return None
        if not 1 <= number <= len(items):
            print('Такого номера нет')
            return None
        return items[number - 1]

    def _buy(self, item: Food | Medicine, bag: list[Any]) -> None:
        """Оплатить выбранный товар и добавить его в инвентарь.

        Raises:
            NotEnoughMoney: Если денег на покупку не хватает.
        """
        if self.coins < item.price:
            raise NotEnoughMoney('Не хватает монет')
        self.coins -= item.price
        if isinstance(item, Medicine):
            bag.append(Medicine(
                name=item.name, price=item.price, heal_hp=item.heal_hp,
                number_of_uses=item.number_of_uses,
            ))
        else:
            bag.append(item)

    def buy_food(self) -> None:
        """Купить одну порцию еды из магазина."""
        item = self._choose(self.all_food, 'Доступная еда:')
        if item is not None:
            self._buy(item, self._food)

    def buy_medicine(self) -> None:
        """Купить лекарство из магазина."""
        item = self._choose(self.all_medicine, 'Доступные лекарства:')
        if item is not None:
            self._buy(item, self._medicine)

    def feed_tamagochi(self) -> None:
        """Накормить питомца и израсходовать порцию еды."""
        item = self._choose(self._food, 'Еда в сумке:')
        if item is not None:
            self.tamagochi.feed(item)
            self._food.remove(item)
            self.tamagochi.update()

    def heal_tamagochi(self) -> None:
        """Вылечить питомца одним применением лекарства."""
        item = self._choose(self._medicine, 'Лекарства в сумке:')
        if item is not None:
            self.tamagochi.heal(item)
            if item.is_empty():
                self._medicine.remove(item)
            self.tamagochi.update()

    def rest_tamagochi(self) -> None:
        """Дать питомцу отдохнуть и обновить его потребности."""
        self.tamagochi.rest()
        self.tamagochi.update()

    def play_with_tamagochi(self) -> None:
        """Поиграть с питомцем и обновить его потребности."""
        self.tamagochi.play()
        self.tamagochi.update()

    def get_status(self) -> dict[str, Any]:
        """Вернуть характеристики питомца вместе с балансом монет."""
        return {**self.tamagochi.status, 'coins': self.coins}
