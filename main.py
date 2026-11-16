"""Консольный интерфейс игры «Тамагочи»."""

from game.clicker import SimpleRandomClicker
from game.constants import FOOD_CATALOG, MEDICINE_CATALOG
from game.exceptions import GameError, TamagochiIsGone
from game.game import SimpleGame
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


def main() -> None:
    """Запустить консольную игру и обрабатывать команды пользователя."""
    all_food = [Food(*entry) for entry in FOOD_CATALOG]
    all_medicine = [Medicine(*entry) for entry in MEDICINE_CATALOG]
    game = SimpleGame(
        tamagochi=SimpleTamagochi(),
        clicker=SimpleRandomClicker(),
        all_food=all_food,
        all_medicine=all_medicine,
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
