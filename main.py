"""Консольный интерфейс игры «Тамагочи»."""

from collections.abc import Sequence

from game.clicker import SimpleRandomClicker
from game.constants import FOOD_CATALOG, MEDICINE_CATALOG
from game.exceptions import GameError, TamagochiIsGone
from game.game import ShopItem, SimpleGame
from game.models import Food, Medicine
from game.tamagochi import SimpleTamagochi

STATUS_TEMPLATE = (
    'Голод: {hunger}, усталость: {fatigue}, '
    'здоровье: {hp}, энергия: {energy}, монеты: {coins}'
)
MENU = (
    '1. Работать\n2. Купить еду\n3. Купить лекарство\n'
    '4. Кормить\n5. Лечить\n6. Играть\n7. Отдыхать\n0. Выход'
)


def select_item(items: Sequence[ShopItem], title: str) -> ShopItem | None:
    """Получить выбранный предмет от пользователя.

    Args:
        items: Предметы магазина или инвентаря.
        title: Название предлагаемого списка.

    Returns:
        Выбранный предмет либо None при отмене или неверном номере.
    """
    if not items:
        print('Список пуст')
        return None
    print(title)
    for number, item in enumerate(items, start=1):
        print(f'{number}. {item}')
    answer = input('Номер (0 — отмена): ').strip()
    if not answer.isdecimal():
        print('Нужно ввести номер')
        return None
    index = int(answer)
    if index == 0:
        return None
    if not 1 <= index <= len(items):
        print('Такого номера нет')
        return None
    return items[index - 1]


def main() -> None:
    """Запустить консольную игру и обрабатывать команды пользователя."""
    all_food = [Food(*entry) for entry in FOOD_CATALOG]
    all_medicine = [Medicine(*entry) for entry in MEDICINE_CATALOG]
    game = SimpleGame(
        tamagochi=SimpleTamagochi(),
        clicker=SimpleRandomClicker(),
        all_food=all_food,
        all_medicine=all_medicine,
        selector=select_item,
    )
    actions = {
        '2': game.buy_food,
        '3': game.buy_medicine,
        '4': game.feed_tamagochi,
        '5': game.heal_tamagochi,
        '6': game.play_with_tamagochi,
        '7': game.rest_tamagochi,
    }
    output = 'Добро пожаловать в Тамагочи-кликер!'
    while True:
        if output:
            print(output)
            output = ''
        print(f'\nЕда: {game.food}\nЛекарства: {game.medicine}')
        print(STATUS_TEMPLATE.format(**game.get_status()))
        if game.tamagochi.is_sick():
            print('Питомец заболел. Отдых менее эффективен.')
        print(MENU)
        try:
            command = input('Выберите действие: ').strip()
            if command == '0':
                break
            if command == '1':
                output = f'Заработано {game.work()} монет'
            elif command in actions:
                actions[command]()
            else:
                output = 'Неизвестная команда'
        except TamagochiIsGone:
            print('Игра окончена: питомец погиб.')
            break
        except GameError as error:
            output = str(error)
        except (EOFError, KeyboardInterrupt):
            print('\nИгра завершена.')
            break


if __name__ == '__main__':
    main()
