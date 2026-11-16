"""Проверка контрактов, инкапсуляции и игровых сценариев."""

import contextlib
import io
import unittest
from dataclasses import FrozenInstanceError
from unittest.mock import patch

from game.clicker import AbstractClicker, SimpleRandomClicker
from game.constants import (
    INITIAL_COINS,
    INITIAL_ENERGY,
    INITIAL_FATIGUE,
    INITIAL_HP,
    INITIAL_HUNGER,
)
from game.exceptions import (
    GameError,
    InvalidItemSelection,
    MedicineIsEmpty,
    NotEnoughEnergy,
    NotEnoughMoney,
    TamagochiIsGone,
)
from game.game import AbstractGame, SimpleGame
from game.models import Food, Medicine
from game.tamagochi import AbstractTamagochi, SimpleTamagochi
from main import main, select_item


class TamagochiTests(unittest.TestCase):
    """Проверки отдельных игровых компонентов и их взаимодействия."""

    def setUp(self) -> None:
        """Создать отдельный набор объектов для каждого теста."""
        self.pet = SimpleTamagochi()
        self.clicker = SimpleRandomClicker(10, 20)
        self.apple = Food('Яблоко', 10, 15)
        self.pill = Medicine('Таблетка', 30, 20, 2)
        self.game = SimpleGame(
            self.pet,
            self.clicker,
            [self.apple],
            [self.pill],
        )
        no_sickness = patch('game.tamagochi.random', return_value=1)
        no_sickness.start()
        self.addCleanup(no_sickness.stop)

    def _earn(self, amount: int) -> None:
        """Получить не меньше указанной суммы законным игровым действием."""
        while self.game.coins < amount:
            self.game.work()

    def test_abstract_contracts(self) -> None:
        """Реализации наследуются от установленных интерфейсов."""
        self.assertIsInstance(self.pet, AbstractTamagochi)
        self.assertIsInstance(self.clicker, AbstractClicker)
        self.assertIsInstance(self.game, AbstractGame)

    def test_abstract_types_cannot_be_instantiated(self) -> None:
        """Абстрактные компоненты нельзя создать напрямую."""
        for cls in (AbstractClicker, AbstractTamagochi, AbstractGame):
            with self.subTest(cls=cls), self.assertRaises(TypeError):
                cls()

    def test_initial_state(self) -> None:
        """Начальное состояние определяется константами."""
        self.assertEqual(
            self.pet.status,
            {
                'hunger': INITIAL_HUNGER,
                'fatigue': INITIAL_FATIGUE,
                'hp': INITIAL_HP,
                'energy': INITIAL_ENERGY,
            },
        )
        self.assertEqual(self.game.coins, INITIAL_COINS)

    def test_status_is_independent_dict(self) -> None:
        """Редактирование возвращённого статуса не влияет на питомца."""
        self.pet.status['hp'] = -100
        self.assertEqual(self.pet.status['hp'], INITIAL_HP)

    def test_game_status_is_independent_dict(self) -> None:
        """Редактирование возвращённого статуса не меняет баланс."""
        self.game.get_status()['coins'] = 100000
        self.assertEqual(self.game.coins, INITIAL_COINS)

    def test_pet_name_read_only(self) -> None:
        """Имя питомца доступно для чтения, но не для присваивания."""
        self.assertEqual(self.pet.name, 'Пиксель')
        with self.assertRaises(AttributeError):
            self.pet.name = 'Другое имя'

    def test_pet_state_not_publicly_writable(self) -> None:
        """Характеристики не предоставляют публичных изменяемых полей."""
        for field in ('hunger', 'fatigue', 'hp', 'energy'):
            with self.subTest(field=field):
                self.assertFalse(hasattr(self.pet, field))

    def test_game_balance_read_only(self) -> None:
        """Баланс нельзя изменить через публичное присваивание."""
        with self.assertRaises(AttributeError):
            self.game.coins = 100000

    def test_game_pet_reference_read_only(self) -> None:
        """Нельзя незаметно заменить объект питомца внутри игры."""
        with self.assertRaises(AttributeError):
            self.game.tamagochi = SimpleTamagochi()

    def test_clicker_bounds_are_internal(self) -> None:
        """Границы заработка являются внутренними полями кликера."""
        self.assertFalse(hasattr(self.clicker, 'min_income'))
        self.assertFalse(hasattr(self.clicker, 'max_income'))

    def test_clicker_income_read_only(self) -> None:
        """Начисленный доход можно читать, но не присваивать."""
        with self.assertRaises(AttributeError):
            self.clicker.income_per_click = 1000

    def test_clicker_income_within_range(self) -> None:
        """Каждое начисление ограничено указанным диапазоном."""
        for _ in range(100):
            self.clicker.click()
            self.assertGreaterEqual(self.clicker.income_per_click, 10)
            self.assertLessEqual(self.clicker.income_per_click, 20)

    def test_invalid_clicker_settings(self) -> None:
        """Некорректный диапазон заработка отвергается при создании."""
        for bounds in ((20, 10), (-1, 10)):
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                SimpleRandomClicker(*bounds)

    def test_work_changes_coins_and_pet(self) -> None:
        """Работа начисляет монеты и применяет ровно один ход."""
        earned = self.game.work()
        self.assertEqual(self.game.coins, earned)
        self.assertEqual(self.pet.status['hunger'], 6)
        self.assertEqual(self.pet.status['fatigue'], 4)
        self.assertEqual(self.pet.status['energy'], 96)

    def test_work_without_console(self) -> None:
        """Игровая логика работы не вызывает input или print."""
        with (
            patch('builtins.input', side_effect=AssertionError('input used')),
            patch('builtins.print', side_effect=AssertionError('print used')),
        ):
            self.game.work()

    def test_food_purchase(self) -> None:
        """Покупка уменьшает баланс и добавляет порцию."""
        self._earn(15)
        before = self.game.coins
        self.game.buy_food()
        self.assertEqual(self.game.coins, before - 15)
        self.assertEqual(self.game.food, [self.apple])

    def test_food_purchase_causes_tick(self) -> None:
        """Успешная покупка считается одним игровым действием."""
        self._earn(15)
        before = self.pet.status['hunger']
        self.game.buy_food()
        self.assertEqual(self.pet.status['hunger'], before + 6)

    def test_not_enough_money(self) -> None:
        """Покупка без монет вызывает специальное игровое исключение."""
        with self.assertRaises(NotEnoughMoney):
            self.game.buy_food()
        self.assertEqual(self.game.coins, 0)
        self.assertEqual(self.game.food, [])
        self.assertEqual(self.pet.status['hunger'], 0)

    def test_food_inventory_snapshot(self) -> None:
        """Копию списка еды нельзя использовать для изменения инвентаря."""
        self._earn(15)
        self.game.buy_food()
        self.game.food.clear()
        self.assertEqual(self.game.food, [self.apple])

    def test_food_model_is_immutable(self) -> None:
        """Параметры еды нельзя изменять после создания."""
        with self.assertRaises(FrozenInstanceError):
            self.apple.price = 0

    def test_food_consumption(self) -> None:
        """Кормление расходует порцию и изменяет голод."""
        self._earn(15)
        self.game.buy_food()
        self.pet._hunger = 50
        self.game.feed_tamagochi()
        self.assertEqual(self.pet.status['hunger'], 46)
        self.assertEqual(self.game.food, [])

    def test_overfeeding_not_negative_hunger(self) -> None:
        """Переизбыток насыщения не делает голод отрицательным."""
        self.pet.feed(Food('Сытная еда', 1000, 0))
        self.assertEqual(self.pet.status['hunger'], 0)

    def test_empty_inventory_no_tick(self) -> None:
        """Кормление без еды не меняет состояние."""
        self.game.feed_tamagochi()
        self.assertEqual(self.pet.status['hunger'], 0)

    def test_medicine_purchase_creates_copy(self) -> None:
        """Купленный препарат отличается от экземпляра магазина."""
        self._earn(30)
        self.game.buy_medicine()
        self.assertEqual(len(self.game.medicine), 1)
        self.assertIsNot(self.game.medicine[0], self.pill)
        self.assertEqual(self.pill.uses, 0)

    def test_medicine_inventory_snapshot(self) -> None:
        """Внешняя мутация копии лекарства не тратит реальные дозы."""
        self._earn(30)
        self.game.buy_medicine()
        self.game.medicine[0].use()
        self.game.medicine.clear()
        self.assertEqual(self.game.medicine[0].uses, 0)

    def test_medicine_use_and_exhaustion(self) -> None:
        """Medicine.use проверяет и расходует ровно одну дозу."""
        self.pill.use()
        self.assertEqual(self.pill.uses, 1)
        self.pill.use()
        self.assertTrue(self.pill.is_empty())
        self.assertEqual(self.pill.uses, 2)
        with self.assertRaises(MedicineIsEmpty):
            self.pill.use()
        self.assertEqual(self.pill.uses, 2)

    def test_medicine_heal_uses_model_method(self) -> None:
        """Питомец лечится через публичный метод Medicine.use."""
        with patch.object(self.pill, 'use', wraps=self.pill.use) as use:
            self.pet.heal(self.pill)
        use.assert_called_once_with()

    def test_exhausted_medicine_exception(self) -> None:
        """Лечение пустым препаратом выдаёт игровой тип ошибки."""
        self.pill.use()
        self.pill.use()
        with self.assertRaises(MedicineIsEmpty):
            self.pet.heal(self.pill)

    def test_heal_consumes_and_removes_medicine(self) -> None:
        """Израсходованная упаковка удаляется после второй дозы."""
        self._earn(30)
        self.game.buy_medicine()
        self.pet._hp = 30
        self.game.heal_tamagochi()
        self.assertEqual(self.game.medicine[0].uses, 1)
        self.game.heal_tamagochi()
        self.assertEqual(self.game.medicine, [])
        self.assertEqual(self.pet.status['hp'], 70)

    def test_heal_removes_sickness(self) -> None:
        """Применение лекарства снимает болезнь."""
        self.pet._sick = True
        self.pet.heal(self.pill)
        self.assertFalse(self.pet.is_sick())

    def test_zero_health_is_alive(self) -> None:
        """По условиям здоровье ровно ноль не завершает игру."""
        self.pet._hp = 0
        self.assertTrue(self.pet.is_alive())

    def test_negative_health_ends_game(self) -> None:
        """При здоровье ниже нуля питомец погибает."""
        self.pet._hp = 0
        self.pet._sick = True
        with self.assertRaises(TamagochiIsGone):
            self.pet.update()
        self.assertFalse(self.pet.is_alive())

    def test_dead_pet_cannot_act(self) -> None:
        """Действия погибшего питомца запрещены."""
        self.pet._hp = -1
        with self.assertRaises(TamagochiIsGone):
            self.pet.feed(self.apple)

    def test_play_costs_energy(self) -> None:
        """Игровое действие снижает энергию."""
        self.pet.play()
        self.assertEqual(self.pet.status['energy'], 90)
        self.assertEqual(self.pet.status['fatigue'], 7)

    def test_play_requires_energy(self) -> None:
        """Нехватка энергии вызывает NotEnoughEnergy."""
        self.pet._energy = 5
        with self.assertRaises(NotEnoughEnergy):
            self.pet.play()
        self.assertEqual(self.pet.status['energy'], 5)

    def test_failed_play_does_not_tick(self) -> None:
        """Недопустимая игра через Game не изменяет состояние."""
        self.pet._energy = 5
        with self.assertRaises(NotEnoughEnergy):
            self.game.play_with_tamagochi()
        self.assertEqual(self.pet.status['hunger'], 0)

    def test_rest_restores_energy(self) -> None:
        """Отдых восстанавливает энергию и снижает усталость."""
        self.pet._energy = 20
        self.pet._fatigue = 50
        self.pet.rest()
        self.assertEqual(self.pet.status['energy'], 45)
        self.assertEqual(self.pet.status['fatigue'], 25)

    def test_sick_rest_is_weaker(self) -> None:
        """Больной питомец восстанавливается медленнее."""
        self.pet._energy = 20
        self.pet._sick = True
        self.pet.rest()
        self.assertEqual(self.pet.status['energy'], 32)

    def test_disease_can_appear(self) -> None:
        """При неблагоприятном случайном событии питомец заболевает."""
        with patch('game.tamagochi.random', return_value=0):
            self.pet.update()
        self.assertTrue(self.pet.is_sick())
        self.assertEqual(self.pet.status['hp'], 96)

    def test_tick_increases_needs(self) -> None:
        """Один ход изменяет потребности питомца."""
        self.pet.update()
        self.assertEqual(self.pet.status['hunger'], 6)
        self.assertEqual(self.pet.status['fatigue'], 4)
        self.assertEqual(self.pet.status['energy'], 96)

    def test_selected_item_must_be_from_available_items(self) -> None:
        """Нельзя купить объект, не присутствующий в каталоге."""
        other = SimpleGame(
            self.pet,
            self.clicker,
            [self.apple],
            [],
            selector=lambda items, title: Food('Чужой', 100, 0),
        )
        with self.assertRaises(InvalidItemSelection):
            other.buy_food()

    def test_choose_cancel_does_not_advance_game(self) -> None:
        """Отмена выбора не расходует игровой ход."""
        other = SimpleGame(
            self.pet,
            self.clicker,
            [self.apple],
            [],
            selector=lambda items, title: None,
        )
        other.buy_food()
        self.assertEqual(self.pet.status['hunger'], 0)

    def test_game_does_not_call_console(self) -> None:
        """Game не зависит от консольного ввода и вывода."""
        self._earn(15)
        with (
            patch('builtins.input', side_effect=AssertionError('input used')),
            patch('builtins.print', side_effect=AssertionError('print used')),
        ):
            self.game.buy_food()
        self.assertEqual(self.game.food, [self.apple])

    def test_game_state_contains_expected_fields(self) -> None:
        """Статус игры соответствует исходному контракту."""
        self.assertEqual(
            set(self.game.get_status()),
            {'hunger', 'fatigue', 'hp', 'energy', 'coins'},
        )

    def test_choose_valid_option_from_console(self) -> None:
        """Консольный интерфейс возвращает выбранный предмет."""
        with (
            patch('builtins.input', return_value='1'),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertIs(select_item([self.apple], 'Еда'), self.apple)

    def test_choose_invalid_option(self) -> None:
        """Неверный номер возвращает None."""
        with (
            patch('builtins.input', return_value='abc'),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertIsNone(select_item([self.apple], 'Еда'))

    def test_game_exceptions_share_base_class(self) -> None:
        """Игровые ошибки объединены общим классом."""
        for cls in (
            TamagochiIsGone,
            NotEnoughMoney,
            NotEnoughEnergy,
            MedicineIsEmpty,
            InvalidItemSelection,
        ):
            self.assertTrue(issubclass(cls, GameError))

    def test_console_starts_and_exits(self) -> None:
        """Игровой цикл корректно завершает работу по команде ноль."""
        output = io.StringIO()
        with (
            patch('builtins.input', return_value='0'),
            contextlib.redirect_stdout(output),
        ):
            main()
        self.assertIn('Добро пожаловать', output.getvalue())

    def test_console_work_and_exit(self) -> None:
        """Работа и выход проходят через консольное меню."""
        output = io.StringIO()
        with (
            patch('builtins.input', side_effect=['1', '0']),
            contextlib.redirect_stdout(output),
        ):
            main()
        self.assertIn('Заработано', output.getvalue())

    def test_console_invalid_command(self) -> None:
        """Неизвестная команда не завершает игровой цикл."""
        output = io.StringIO()
        with (
            patch('builtins.input', side_effect=['bad', '0']),
            contextlib.redirect_stdout(output),
        ):
            main()
        self.assertIn('Неизвестная команда', output.getvalue())

    def test_console_handles_game_exception(self) -> None:
        """Ожидаемая игровая ошибка выводится через сообщение."""
        output = io.StringIO()
        with (
            patch('builtins.input', side_effect=['6', '0']),
            patch(
                'main.SimpleTamagochi.play',
                side_effect=NotEnoughEnergy('Нет энергии'),
            ),
            contextlib.redirect_stdout(output),
        ):
            main()
        self.assertIn('Нет энергии', output.getvalue())

    def test_unexpected_value_error_is_not_suppressed(self) -> None:
        """Ошибки программирования не маскируются как игровые."""
        with (
            patch('builtins.input', return_value='6'),
            patch(
                'main.SimpleTamagochi.play',
                side_effect=ValueError('ошибка'),
            ),
            contextlib.redirect_stdout(io.StringIO()),
            self.assertRaisesRegex(ValueError, 'ошибка'),
        ):
            main()

    def test_console_game_over(self) -> None:
        """Гибель питомца завершает цикл с сообщением."""
        output = io.StringIO()
        with (
            patch('builtins.input', side_effect=['1', '0']),
            patch(
                'main.SimpleTamagochi.update',
                side_effect=TamagochiIsGone('Питомец погиб'),
            ),
            contextlib.redirect_stdout(output),
        ):
            main()
        self.assertIn('Игра окончена', output.getvalue())


if __name__ == '__main__':
    unittest.main()
