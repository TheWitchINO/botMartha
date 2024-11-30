# messages.py
import vk_api
from config import token
import random
import re

vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()

def send_message(peer_id, message):
    vk.messages.send(peer_id=peer_id, message=message, random_id=0)

def get_user_name(user_id):
    user_info = vk.users.get(user_ids=user_id)
    if user_info:
        return user_info[0].get('first_name', "друг")
    return "друг"

def roll_dice(sides, rolls=1):
    results = [random.randint(1, sides) for _ in range(rolls)]
    return results

help_message = (
    "Здравствуй, авантюрист! Я помогу тебе разобраться с системой бросков кубиков:\n\n"
    "🎲 **Основные команды для бросков кубиков:**\n"
    "- `/д20` — бросить один 20-гранный кубик.\n"
    "- `/3д6` — бросить три 6-гранных кубика и показать сумму.\n"
    "- `/д20+5` — бросить один 20-гранный кубик и добавить модификатор +5.\n"
    "📋 **Примеры команд:**\n"
    "- `/д20` — обычный бросок 20-гранного кубика.\n"
    "- `/2д10+3` — бросить два 10-гранных кубика и добавить модификатор +3.\n"
    "Напиши `/помощь`, если тебе снова понадобится эта инструкция. Удачи в бросках! 🎲")


def calculate_roll(command: str) -> str:
    """
    Обрабатывает команду броска кубиков.
    :param command: Команда в формате "к20", "2к6+3" и т.п.
    :return: Результат броска в текстовом формате.
    """
    # Заменяем все "к" на "д" для правильной обработки
    command = command.replace("к", "д").replace("d", "д")

    message = ""

    # Разбиваем команду по регулярным выражениям, чтобы отделить команды бросков и модификаторы
    parts = re.findall(r'(\d*д\d+)([+-]?\d*)', command)

    if not parts:
        return "Некорректная команда. Убедитесь в правильности формата, например: /д20+5."

    try:
        for part in parts:
            dice_command, modifier = part
            part_message = ""

            if "д" in dice_command:  # Проверяем, что есть символ "д", указывающий на бросок кубика
                # Разделяем на количество кубиков и количество граней
                dice_count, dice_sides = dice_command.split("д")

                # Проверка на правильность чисел
                if not dice_sides.isdigit() or (dice_count and not dice_count.isdigit()):
                    raise ValueError("Некорректный формат чисел в команде.")

                dice_count = int(dice_count) if dice_count else 1
                dice_sides = int(dice_sides)

                if dice_count <= 0 or dice_sides <= 0:
                    raise ValueError("Количество кубиков и граней должно быть положительным числом.")

                # Бросок кубика
                rolls = roll_dice(dice_sides, dice_count)
                rolls_str = ", ".join(map(str, rolls))

                if dice_count == 1 and dice_sides == 20:
                    crit = "Критический успех!" if rolls[0] == 20 else "Критический провал!" if rolls[0] == 1 else ""
                    part_message += f"Результат броска: {rolls[0]}. {crit}\n"
                elif dice_count >= 2:
                    part_message += f"Результаты бросков: {rolls_str}.\n"
                else:
                    part_message += f"Результат броска: {rolls[0]}\n"

            # Обрабатываем модификатор для каждой команды отдельно
            if modifier:
                try:
                    modifier_value = int(modifier)
                    total = sum(rolls) + modifier_value
                    part_message += f" Итог: {', '.join(map(str, rolls))} + {modifier_value} = {total}.\n"
                except ValueError:
                    part_message += "Некорректный модификатор. Убедитесь, что модификатор — это число.\n"

            message += part_message  # Добавляем результат обработки каждой команды

    except ValueError as e:
        return f"Ошибка: {str(e)}"

    return message













