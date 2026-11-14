"""Точка входа консольной игры «Тамагочи»."""

from game.clicker import SimpleRandomClicker
from game.exceptions import NotEnoughMoney, TamagochiIsGone
from game.game import SimpleGame
from game.models import Food, Medicine
from game.tamagochi import SimpleTamagochi


def main() -> None:
    """Запустить игру и обрабатывать команды до выхода или гибели питомца."""
    all_food = [
        Food(name='Бургер', satiety=20, price=40),
        Food(name='Салат', satiety=10, price=20),
        Food(name='Яблоко', satiety=10, price=15),
    ]
    all_medicine = [
        Medicine(name='Ибупрофен', price=30, heal_hp=20, number_of_uses=2),
    ]
    game = SimpleGame(
        SimpleTamagochi(), SimpleRandomClicker(10, 20),
        all_food=all_food, all_medicine=all_medicine,
    )
    print('Добро пожаловать в Тамагочи-кликер!')

    actions = {
        '2': game.buy_food,
        '3': game.buy_medicine,
        '4': game.feed_tamagochi,
        '5': game.heal_tamagochi,
        '6': game.play_with_tamagochi,
        '7': game.rest_tamagochi,
    }
    while True:
        status = game.get_status()
        print(f'\nЕда: {game.food}\nЛекарства: {game.medicine}')
        print(
            f"Голод: {status['hunger']}, усталость: {status['fatigue']}, "
            f"здоровье: {status['hp']}, энергия: {status['energy']}, "
            f"монеты: {status['coins']}"
        )
        if game.tamagochi.is_sick():
            print('Питомец заболел. Отдых менее эффективен.')
        print('1. Работать\n2. Купить еду\n3. Купить лекарство')
        print('4. Кормить\n5. Лечить\n6. Играть\n7. Отдыхать\n0. Выход')
        try:
            command = input('Выберите действие: ').strip()
            if command == '0':
                break
            if command == '1':
                income = game.work()
                print(f'Заработано {income} монет')
                game.tamagochi.update()
            elif command in actions:
                actions[command]()
            else:
                print('Неизвестная команда')
        except (NotEnoughMoney, ValueError) as error:
            print(error)
        except TamagochiIsGone:
            print('Игра окончена: питомец погиб.')
            break
        except (EOFError, KeyboardInterrupt):
            print('\nИгра завершена.')
            break


if __name__ == '__main__':
    main()
