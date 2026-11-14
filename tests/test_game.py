"""Проверка основных контрактов и игровых сценариев."""

import contextlib
import io
import unittest
from unittest.mock import patch

from game.clicker import AbstractClicker, SimpleRandomClicker
from game.exceptions import NotEnoughMoney, TamagochiIsGone
from game.game import AbstractGame, SimpleGame
from game.models import Food, Medicine
from game.tamagochi import AbstractTamagochi, SimpleTamagochi


class TamagochiTests(unittest.TestCase):
    """Проверка игровых компонентов."""

    def setUp(self) -> None:
        """Создать отдельное состояние для каждого теста."""
        self.pet = SimpleTamagochi()
        self.clicker = SimpleRandomClicker(10, 20)
        self.apple = Food('Яблоко', 10, 15)
        self.pill = Medicine('Таблетка', 30, 20, 2)
        self.game = SimpleGame(
            self.pet, self.clicker, [self.apple], [self.pill]
        )

    def test_inheritance(self) -> None:
        """Проверить реализацию всех абстрактных контрактов."""
        self.assertIsInstance(self.pet, AbstractTamagochi)
        self.assertIsInstance(self.clicker, AbstractClicker)
        self.assertIsInstance(self.game, AbstractGame)

    def test_initial_stats(self) -> None:
        """Проверить исходные характеристики."""
        self.assertEqual(self.pet.status['hp'], 100)
        self.assertEqual(self.pet.status['energy'], 100)
        self.assertEqual(self.game.get_status()['coins'], 0)

    def test_status_is_copy(self) -> None:
        """Проверить защиту состояния от изменения извне."""
        self.pet.status['hp'] = -99
        self.assertEqual(self.pet.hp, 100)

    def test_click_income_bounds(self) -> None:
        """Проверить диапазон случайного дохода."""
        for _ in range(100):
            self.clicker.click()
            self.assertGreaterEqual(self.clicker.income_per_click, 10)
            self.assertLessEqual(self.clicker.income_per_click, 20)

    def test_invalid_clicker_bounds(self) -> None:
        """Проверить отклонение некорректных границ дохода."""
        with self.assertRaises(ValueError):
            SimpleRandomClicker(20, 10)

    def test_work_increases_coins(self) -> None:
        """Проверить начисление заработка."""
        earned = self.game.work()
        self.assertEqual(self.game.coins, earned)
        self.assertGreaterEqual(earned, 10)

    def test_purchase_food(self) -> None:
        """Проверить списание и добавление еды."""
        self.game.coins = 30
        with patch('builtins.input', return_value='1'):
            self.game.buy_food()
        self.assertEqual(self.game.coins, 15)
        self.assertEqual(self.game.food, [self.apple])

    def test_not_enough_money(self) -> None:
        """Проверить отклонение покупки без денег."""
        with patch('builtins.input', return_value='1'):
            with self.assertRaises(NotEnoughMoney):
                self.game.buy_food()
        self.assertEqual(self.game.food, [])

    def test_cancel_purchase(self) -> None:
        """Проверить отмену выбора товара."""
        self.game.coins = 50
        with patch('builtins.input', return_value='0'):
            self.game.buy_food()
        self.assertEqual(self.game.coins, 50)

    def test_invalid_selection(self) -> None:
        """Проверить безопасный ввод номера товара."""
        with patch('builtins.input', return_value='не число'):
            self.game.buy_food()
        self.assertEqual(self.game.food, [])

    def test_feed_consumes_one_item(self) -> None:
        """Проверить кормление и удаление порции."""
        self.pet.hunger = 50
        self.game.food.append(self.apple)
        with patch('builtins.input', return_value='1'):
            self.game.feed_tamagochi()
        self.assertEqual(self.pet.hunger, 46)
        self.assertEqual(self.game.food, [])

    def test_feed_clamps_hunger(self) -> None:
        """Проверить нижнюю границу голода."""
        self.pet.feed(Food('Сытная еда', 999, 0))
        self.assertEqual(self.pet.hunger, 0)

    def test_purchase_medicine_independent_copy(self) -> None:
        """Проверить независимость купленной упаковки."""
        self.game.coins = 70
        with patch('builtins.input', return_value='1'):
            self.game.buy_medicine()
        self.assertEqual(self.game.coins, 40)
        self.assertEqual(len(self.game.medicine), 1)
        self.assertIsNot(self.game.medicine[0], self.pill)

    def test_medicine_uses_and_removal(self) -> None:
        """Проверить два применения лекарства."""
        self.pet.hp = 30
        self.game.medicine.append(self.pill)
        with patch('builtins.input', return_value='1'):
            self.game.heal_tamagochi()
            self.game.heal_tamagochi()
        self.assertEqual(self.pet.hp, 70)
        self.assertEqual(self.pill.uses, 2)
        self.assertEqual(self.game.medicine, [])

    def test_exhausted_medicine(self) -> None:
        """Проверить запрет применения пустого лекарства."""
        self.pill.uses = 2
        with self.assertRaises(ValueError):
            self.pet.heal(self.pill)

    def test_play_consumes_energy(self) -> None:
        """Проверить расходы энергии на игру."""
        self.pet.play()
        self.assertEqual(self.pet.energy, 90)

    def test_play_low_energy(self) -> None:
        """Проверить запрет игры при нехватке энергии."""
        self.pet.energy = 5
        with self.assertRaises(ValueError):
            self.pet.play()

    def test_rest_restores_energy(self) -> None:
        """Проверить восстановление сил."""
        self.pet.energy = 20
        self.pet.fatigue = 50
        self.pet.rest()
        self.assertEqual(self.pet.energy, 45)
        self.assertEqual(self.pet.fatigue, 25)

    def test_sick_rest_less_effective(self) -> None:
        """Проверить ослабление отдыха при болезни."""
        self.pet._sick = True
        self.pet.energy = 20
        self.pet.rest()
        self.assertEqual(self.pet.energy, 32)

    def test_healing_removes_sickness(self) -> None:
        """Проверить выздоровление после лечения."""
        self.pet._sick = True
        self.pet.heal(self.pill)
        self.assertFalse(self.pet.is_sick())

    def test_update_changes_state(self) -> None:
        """Проверить изменение состояния за игровой ход."""
        with patch('game.tamagochi.random', return_value=1):
            self.pet.update()
        self.assertEqual(self.pet.hunger, 6)
        self.assertEqual(self.pet.fatigue, 4)
        self.assertEqual(self.pet.energy, 96)

    def test_sickness_can_start(self) -> None:
        """Проверить возможность заболеть."""
        with patch('game.tamagochi.random', return_value=0):
            self.pet.update()
        self.assertTrue(self.pet.is_sick())
        self.assertEqual(self.pet.hp, 96)

    def test_game_over_below_zero(self) -> None:
        """Проверить завершение игры после смерти."""
        self.pet.hp = 0
        self.pet._sick = True
        with self.assertRaises(TamagochiIsGone):
            self.pet.update()
        self.assertFalse(self.pet.is_alive())

    def test_zero_health_not_dead(self) -> None:
        """Проверить буквальное условие смерти ниже нуля."""
        self.pet.hp = 0
        self.assertTrue(self.pet.is_alive())

    def test_game_status_includes_all_stats(self) -> None:
        """Проверить возвращаемые поля игрового статуса."""
        self.assertEqual(
            set(self.game.get_status()),
            {'hunger', 'fatigue', 'hp', 'energy', 'coins'},
        )

    def test_console_entry_exit(self) -> None:
        """Проверить запуск и корректный выход консольного цикла."""
        from main import main
        output = io.StringIO()
        with patch('builtins.input', return_value='0'):
            with contextlib.redirect_stdout(output):
                main()
        self.assertIn('Добро пожаловать', output.getvalue())

    def test_console_work_then_exit(self) -> None:
        """Проверить работу игрового меню на двух ходах."""
        from main import main
        output = io.StringIO()
        with patch('builtins.input', side_effect=['1', '0']):
            with contextlib.redirect_stdout(output):
                main()
        self.assertIn('Заработано', output.getvalue())

    def test_console_invalid_action_then_exit(self) -> None:
        """Проверить обработку неизвестной команды."""
        from main import main
        output = io.StringIO()
        with patch('builtins.input', side_effect=['oops', '0']):
            with contextlib.redirect_stdout(output):
                main()
        self.assertIn('Неизвестная команда', output.getvalue())


if __name__ == '__main__':
    unittest.main()
