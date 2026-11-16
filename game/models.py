"""Данные о еде и лекарствах игрового магазина."""

from dataclasses import dataclass

from .exceptions import MedicineIsEmpty


@dataclass(frozen=True, slots=True)
class Food:
    """Сведения о продукте питания."""

    name: str
    satiety: int
    price: int

    def __repr__(self) -> str:
        """Вернуть описание продукта для меню.

        Returns:
            Название продукта, его стоимость и насыщение.
        """
        return (
            f'{self.name} стоимость: {self.price}, '
            f'утоляет голод на {self.satiety} единиц'
        )


@dataclass
class Medicine:
    """Лекарство с ограниченным количеством использований."""

    name: str
    price: int
    heal_hp: int
    number_of_uses: int
    uses: int = 0

    def is_empty(self) -> bool:
        """Проверить наличие применений.

        Returns:
            True, если все применения уже израсходованы.
        """
        return self.uses >= self.number_of_uses

    def use(self) -> None:
        """Использовать одну дозу лекарства.

        Raises:
            MedicineIsEmpty: Если доступных доз не осталось.
        """
        if self.is_empty():
            raise MedicineIsEmpty('Лекарство закончилось')
        self.uses += 1

    def __repr__(self) -> str:
        """Вернуть описание лекарства для меню.

        Returns:
            Название, стоимость, восстановление HP и запас доз.
        """
        available = max(0, self.number_of_uses - self.uses)
        return (
            f'{self.name} стоимость: {self.price}, '
            f'лечит на {self.heal_hp} HP, '
            f'использований: {available}/{self.number_of_uses}'
        )
