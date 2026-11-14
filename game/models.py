"""Модели товаров игрового магазина."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Food:
    """Еда с насыщением и стоимостью."""

    name: str
    satiety: int
    price: int

    def __repr__(self) -> str:
        """Вернуть описание еды для меню."""
        return (f'{self.name} стоимость: {self.price}, '
                f'утоляет голод на {self.satiety} единиц')


@dataclass
class Medicine:
    """Лекарство с ограниченным количеством применений."""

    name: str
    price: int
    heal_hp: int
    number_of_uses: int
    uses: int = 0

    def is_empty(self) -> bool:
        """Вернуть True, если все применения израсходованы."""
        return self.uses >= self.number_of_uses

    def __repr__(self) -> str:
        """Вернуть описание лекарства для меню."""
        left = max(0, self.number_of_uses - self.uses)
        return (f'{self.name} стоимость: {self.price}, '
                f'лечит на {self.heal_hp} HP, '
                f'использований: {left}/{self.number_of_uses}')
