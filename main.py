from tokenize import group
from typing import Dict, Any
import random
import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from config import token, group_id
from controllers.diceController import calculate_roll
from controllers.messageController import (
    burn_command,
    devour_command,  # NEW
    choose_option,
    get_random_joke,
    hug_command,
    kiss_command,
    bonk_command,
    slap_command,
    send_message,
    get_user_name,
    help_message,
)
from controllers.duelController import DuelController
from controllers.bingoController import BingoController
from controllers.characterController import CharacterController
from controllers.marriageController import MarriageController
from controllers.profileController import ProfileController
from controllers.rouletteController import RouletteController
from controllers.adminController import AdminController
from controllers.lotteryController import LotteryController

# --- VK init ---
vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, group_id=group_id, wait=60)
vk = vk_session.get_api()

marriage_controller = MarriageController()
profile_controller = ProfileController()
roulette_controller = RouletteController()
bingoController = BingoController()
characterController = CharacterController()
adminController = AdminController()
lotteryController = LotteryController()

# ---------------- Main loop -----------------
for event in longpoll.listen():
    if event.type != VkBotEventType.MESSAGE_NEW:
        continue

    # -------- Парсинг входного сообщения --------
    message = event.obj.message
    original_text = message["text"].strip()
    text = original_text.lower()

    peer_id = message["peer_id"]
    user_id = message["from_id"]

    user_name = get_user_name(user_id)

    # --- Выбор "или" ---
    if " или " in text:
        response = choose_option(text)
        if response:
            send_message(peer_id, response)
            continue

    # ===== Кубы =====
    if "марта" in text:
        roll_command = text.split("марта", 1)[1].strip()
        send_message(peer_id, calculate_roll(user_name, roll_command))
        continue
    elif "/" in text:
        roll_command = text.split("/", 1)[1].strip()
        send_message(peer_id, calculate_roll(user_name, roll_command))
        continue

    # ===== Общие фразы =====
    if text == "привет":
        send_message(peer_id, f"Здравствуйте, {user_name}! Чем могу помочь?")
        continue
    if text == "пока":
        send_message(peer_id, f"Удачи вам, {user_name}!")
        continue
    if text == "помощь":
        send_message(peer_id, help_message)
        continue
    if text == "анекдот":
        send_message(peer_id, get_random_joke())
        continue

    # ===== Дуэли =====
    if text == "дуэль":
        if message.get('reply_message'):
            response = DuelController.handle_duel_command(user_id, message['reply_message'])
        else:
            response = DuelController.handle_duel_command(user_id)
        send_message(peer_id, response)
        continue

    if text == "принять дуэль":
        send_message(peer_id, DuelController.handle_accept_duel(user_id))
        continue

    if text == "выстрел":
        send_message(peer_id, DuelController.handle_shoot_command(peer_id, user_id))
        continue

    if text == "дуэль стата":
        stats = DuelController.get_stats(peer_id)
        if not stats:
            send_message(peer_id, 'Статистика дуэлей пока пуста.')
        else:
            response = 'Статистика побед в дуэлях:\n'
            for uid, user_stats in stats.items():
                uname = get_user_name(uid)
                wins = user_stats["wins"]
                streak = user_stats["streak"]
                rank = DuelController.get_rank(wins)
                streak_info = f" | Серия: {streak}🔥" if streak >= 1 else ""
                response += f'{uname}: {wins} ({rank}){streak_info}\n'
            send_message(peer_id, response)
        continue

    # ===== Брак =====
    if text == "брак":
        if message.get('reply_message'):
            response = marriage_controller.propose_marriage(user_id, peer_id, message['reply_message'])
        else:
            response = marriage_controller.propose_marriage(user_id, peer_id)
        send_message(peer_id, response)
        continue

    if text == "принять брак":
        send_message(peer_id, marriage_controller.accept_marriage(user_id))
        continue

    if text == "развод":
        send_message(peer_id, marriage_controller.divorce(user_id, peer_id))
        continue

    if text == "подтвердить развод":
        send_message(peer_id, marriage_controller.confirm_divorce(user_id))
        continue

    if text == "браки":
        marriages = marriage_controller.get_marriages(peer_id)
        if not marriages:
            response = 'В нашей гильдии пока никто не в браке!'
        else:
            response = 'Список браков:\n'
            for pair, data in marriages.items():
                id1, id2 = eval(pair)
                response += f"{get_user_name(id1)} + {get_user_name(id2)} (с {data['date']})\n"
        send_message(peer_id, response)
        continue

    # ===== Профиль =====
    if text.startswith("мне ник"):
        nickname = original_text[len("мне ник"):].strip()
        if nickname:
            profile_controller.set_nickname(user_id, nickname)
            send_message(peer_id, f"Ваш никнейм изменён на '{nickname}'.")
        else:
            send_message(peer_id, "Пожалуйста, укажите никнейм после команды 'мне ник'.")
        continue

    # ===== Эмоции =====
    if text.startswith("обнять"):
        reply_msg = event.message.get('reply_message')
        send_message(peer_id, hug_command(user_id, reply_msg))
        continue

    if text == "погладить":
        if message.get('reply_message'):
            target_id = message['reply_message']['from_id']
            target_name = get_user_name(target_id)
            user_name = get_user_name(user_id)
            
            if target_id == user_id:
                response = f"😅 {user_name}, нельзя гладить себя!"
            else:
                responses = [
                    f"😊 {user_name} нежно погладил(а) {target_name} по голове",
                    f"🥰 {user_name} ласково погладил(а) {target_name}",
                    f"😌 {user_name} успокаивающе погладил(а) {target_name}",
                    f"💕 {user_name} с любовью погладил(а) {target_name}",
                    f"😇 {user_name} заботливо погладил(а) {target_name}"
                ]
                response = random.choice(responses)
        else:
            response = "❌ Чтобы погладить, ответьте на сообщение пользователя!"
        send_message(peer_id, response)
        continue

    if text.startswith("поцеловать"):
        reply_msg = event.message.get('reply_message')
        send_message(peer_id, kiss_command(user_id, reply_msg))
        continue

    if text.startswith("сжечь"):
        reply_msg = event.message.get('reply_message')
        resp, img_path = burn_command(user_id, reply_msg)
        send_message(peer_id, resp, image_path=img_path)  # FIX: keyword arg
        continue

    if text.startswith("сожрать"):
        reply_msg = event.message.get('reply_message')
        resp, doc_path = devour_command(user_id, reply_msg)
        send_message(peer_id, resp, doc_path=doc_path)
        continue

    if text.startswith("шлёпнуть") or text.startswith("шлепнуть"):
        reply_msg = event.message.get('reply_message')
        send_message(peer_id, slap_command(user_id, reply_msg))
        continue

    if text.startswith("боньк"):
        reply_msg = event.message.get('reply_message')
        send_message(peer_id, bonk_command(user_id, reply_msg))
        continue

    # ===== Рулетка =====
    if text == "рулетка":
        send_message(peer_id, roulette_controller.start_game(peer_id, user_id))
        continue

    if text == "рулетка вступить":
        send_message(peer_id, roulette_controller.join_game(peer_id, user_id))
        continue

    if text == "рулетка начать":
        send_message(peer_id, roulette_controller.start_roulette(peer_id))
        continue

    if text == "щелчок":
        send_message(peer_id, roulette_controller.shoot(peer_id, user_id))
        continue

    # Команды для игры в лото
    if text == "лото":
            response = bingoController.start_game(peer_id, user_id)
            send_message(peer_id, response)
            continue

    if text == "лото вступить":
            response = bingoController.join_game(peer_id, user_id)
            send_message(peer_id, response)
            continue

    if text == "лото начать":
            response = bingoController.start_bingo(peer_id, user_id)
            send_message(peer_id, response)
            continue

    if text == "лото число":
            response = bingoController.draw_number(peer_id, user_id)
            send_message(peer_id, response)
            continue

    if text == "лото карточка":
            response = bingoController.check_card(peer_id, user_id)
            send_message(peer_id, response)
            continue

    if text == "лото числа":
            response = bingoController.get_drawn_numbers(peer_id)
            send_message(peer_id, response)
            continue

    if text == "лото результаты":
            response = bingoController.get_standings(peer_id)
            send_message(peer_id, response)
            continue

    # Команда для читерства (подделка случайного числа)
    if text == "лото подделать":
            response = bingoController.cheat_attempt(peer_id, user_id)
            send_message(peer_id, response)
            continue

    if text == "лото читеры":
            response = bingoController.get_excluded_players(peer_id)
            send_message(peer_id, response)
            continue

    if text == "лото стоп":
            response = bingoController.end_game(peer_id, user_id)
            send_message(peer_id, response)
            continue

    # ========= ЛОТЕРЕЯ =========
    # Создание лотереи (только создатель и админы)
    if text == "лотерея":
            if adminController.is_admin(peer_id, user_id):
                response = lotteryController.create_lottery(peer_id, user_id)
            else:
                response = "❌ Только создатель и администраторы могут создавать лотереи!"
            send_message(peer_id, response)
            continue

    # Выдача билетов (только для админа лотереи, работает с упоминаниями и ответами)
    if text.startswith("лотерея билет"):
            parts = text.split()
            if len(parts) >= 3:
                try:
                    # Проверяем, есть ли ответ на сообщение
                    if message.get('reply_message'):
                        target_user_id = message['reply_message']['from_id']
                        count = int(parts[2])
                    else:
                        # Проверяем упоминание в тексте
                        if "[id" in text:
                            # Извлекаем ID из упоминания [id123456|@username]
                            mention_start = text.find("[id") + 3
                            mention_end = text.find("|", mention_start)
                            target_user_id = int(text[mention_start:mention_end])
                            count = int(parts[-1])  # Последнее число - количество
                        else:
                            send_message(peer_id, "❌ Используйте: 'лотерея билет @пользователь количество' или ответьте на сообщение")
                            continue
                    
                    response = lotteryController.give_tickets(peer_id, user_id, target_user_id, count)
                except (ValueError, IndexError):
                    response = "❌ Используйте: 'лотерея билет @пользователь количество' (от 1 до 10)"
            else:
                response = "❌ Используйте: 'лотерея билет @пользователь количество'"
            send_message(peer_id, response)
            continue

    # Мои билеты
    if text == "лотерея мои":
            response = lotteryController.get_my_tickets(peer_id, user_id)
            send_message(peer_id, response)
            continue

    # Список участников
    if text == "лотерея список":
            response = lotteryController.get_participants_list(peer_id)
            send_message(peer_id, response)
            continue

    # Проведение розыгрыша
    if text == "лотерея розыгрыш":
            response = lotteryController.conduct_draw(peer_id, user_id)
            send_message(peer_id, response)
            continue

    # Остановка лотереи
    if text == "лотерея стоп":
            response = lotteryController.stop_lottery(peer_id, user_id)
            send_message(peer_id, response)
            continue

    # ========= СКРЫТЫЕ КОМАНДЫ ЛОТЕРЕИ (только создатель) =========
    # Включение РП-режима
    if text == "лотерея рп вкл":
            if adminController.is_creator(peer_id, user_id):
                response = lotteryController.enable_rp_mode(peer_id, user_id)
            else:
                response = "❌ Команда доступна только создателю беседы!"
            send_message(peer_id, response)
            continue

    # Выключение РП-режима
    if text == "лотерея рп выкл":
            if adminController.is_creator(peer_id, user_id):
                response = lotteryController.disable_rp_mode(peer_id, user_id)
            else:
                response = "❌ Команда доступна только создателю беседы!"
            send_message(peer_id, response)
            continue

    # Установка цены билета
    if text.startswith("лотерея цена"):
            if adminController.is_creator(peer_id, user_id):
                parts = text.split()
                if len(parts) >= 3:
                    try:
                        price = int(parts[2])
                        response = lotteryController.set_ticket_price(peer_id, user_id, price)
                    except ValueError:
                        response = "❌ Укажите корректное число! Пример: 'лотерея цена 150'"
                else:
                    response = "❌ Использование: 'лотерея цена [число]'. Пример: 'лотерея цена 150'"
            else:
                response = "❌ Команда доступна только создателю беседы!"
            send_message(peer_id, response)
            continue

    # Установка количества победителей
    if text.startswith("лотерея победители"):
            if adminController.is_creator(peer_id, user_id) or adminController.is_admin(peer_id, user_id):
                parts = text.split()
                if len(parts) >= 3:
                    try:
                        count = int(parts[2])
                        response = lotteryController.set_winner_count(peer_id, user_id, count)
                    except ValueError:
                        response = "❌ Укажите корректное число! Пример: 'лотерея победители 5'"
                else:
                    response = "❌ Использование: 'лотерея победители [число]'. Пример: 'лотерея победители 5'"
            else:
                response = "❌ Команда доступна только создателю или администраторам беседы!"
            send_message(peer_id, response)
            continue

    # Команды администрирования
    
    # Назначение создателя беседы
    if text == "стать создателем":
            response = adminController.set_creator(peer_id, user_id)
            send_message(peer_id, response)
            continue

    if text == "админка":
            response = adminController.get_chat_staff(peer_id)
            send_message(peer_id, response)
            continue

    if text == "мои права":
            response = adminController.get_user_permissions(peer_id, user_id)
            send_message(peer_id, response)
            continue

    # Проверка прав другого пользователя
    if text == "права":
            try:
                if message.get('reply_message'):
                    target_user_id = message['reply_message']['from_id']
                    response = adminController.get_user_permissions(peer_id, target_user_id)
                else:
                    response = "❌ Ответьте на сообщение пользователя, права которого хотите проверить."
                send_message(peer_id, response)
            except Exception as e:
                send_message(peer_id, "❌ Ошибка при проверке прав пользователя.")
            continue

    if text == "админ помощь":
            response = adminController.get_admin_commands_help(peer_id, user_id)
            send_message(peer_id, response)
            continue

    # Повышение пользователя
    if text == "повысить":
            try:
                if message.get('reply_message'):
                    target_user_id = message['reply_message']['from_id']
                    response = adminController.promote_user(peer_id, user_id, target_user_id)
                else:
                    response = "❌ Ответьте на сообщение пользователя, которого хотите повысить."
                send_message(peer_id, response)
            except Exception as e:
                send_message(peer_id, "❌ Ошибка при повышении пользователя.")
            continue

    # Понижение пользователя
    if text == "понизить":
            try:
                if message.get('reply_message'):
                    target_user_id = message['reply_message']['from_id']
                    response = adminController.demote_user(peer_id, user_id, target_user_id)
                else:
                    response = "❌ Ответьте на сообщение пользователя, которого хотите понизить."
                send_message(peer_id, response)
            except Exception as e:
                send_message(peer_id, "❌ Ошибка при понижении пользователя.")
            continue

    # Кик пользователя
    if text == "кик":
            try:
                if message.get('reply_message'):
                    target_user_id = message['reply_message']['from_id']
                    response = adminController.kick_user(peer_id, user_id, target_user_id, vk)
                else:
                    response = "❌ Ответьте на сообщение пользователя, которого хотите исключить."
                send_message(peer_id, response)
            except Exception as e:
                send_message(peer_id, "❌ Ошибка при исключении пользователя.")
            continue

    # Передача прав создателя
    if text == "передать власть":
            try:
                if message.get('reply_message'):
                    target_user_id = message['reply_message']['from_id']
                    response = adminController.transfer_creator(peer_id, user_id, target_user_id)
                else:
                    response = "❌ Ответьте на сообщение пользователя, которому хотите передать права создателя."
                send_message(peer_id, response)
            except Exception as e:
                send_message(peer_id, "❌ Ошибка при передаче прав создателя.")
            continue

    # Принудительное завершение игр (модераторы и выше)
    if text == "стоп игры":
            if adminController.is_moderator(peer_id, user_id):
                # Завершаем все активные игры
                responses = []
                
                # Завершаем лото
                try:
                    lotto_response = bingoController.force_end_game(peer_id)
                    if not lotto_response.startswith("❌"):
                        responses.append("🎲 Лото завершено")
                except:
                    pass
                
                # Можно добавить завершение других игр
                
                if responses:
                    moderator_name = get_user_name(user_id)
                    final_response = f"⚖️ Модератор {moderator_name} принудительно завершил игры:\n" + "\n".join(responses)
                else:
                    final_response = "❌ Нет активных игр для завершения."
                
                send_message(peer_id, final_response)
            else:
                send_message(peer_id, "❌ Только модераторы и администраторы могут принудительно завершать игры!")
            continue
            
        # Команды для работы с персонажами D&D 5e
    if text == "получить лицензию" or text == "новый персонаж":
            response = characterController.start_character_creation(user_id, peer_id)
            send_message(peer_id, response)

    if text == "лицензия" or text == "лист персонажа":
            response = characterController.get_character_sheet(user_id, peer_id)
            send_message(peer_id, response)

    if text == "сдать лицензию":
            response = characterController.delete_character(user_id, peer_id)
            send_message(peer_id, response)

    else:
            #Условие если команда не найдена.
            pass