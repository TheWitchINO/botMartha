import json
import os
import random
from datetime import datetime
from controllers.messageController import get_user_name

class LotteryController:
    def __init__(self):
        self.data_file = "data/lottery_data.json"
        self.lottery_data = self._load_lottery_data()
        
    def _load_lottery_data(self):
        """Загрузить данные лотереи"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Структура по умолчанию
        return {
            "chats": {},  # {peer_id: {"active": bool, "tickets": {user_id: [numbers]}, "prize_pool": int, "admin": user_id, "rp_mode": bool, "ticket_price": int, "winner_count": int}}
            "global_settings": {
                "default_rp_mode": False,  # РП-режим по умолчанию отключен
                "default_ticket_price": 100,  # Цена билета в золотых по умолчанию
                "default_winner_count": 3  # Количество победителей по умолчанию
            }
        }
    
    def _save_lottery_data(self):
        """Сохранить данные лотереи"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.lottery_data, f, ensure_ascii=False, indent=2)
    
    def _get_chat_settings(self, peer_id):
        """Получить настройки для конкретной беседы"""
        peer_id_str = str(peer_id)
        
        # Инициализируем настройки беседы если их нет
        if "chat_settings" not in self.lottery_data:
            self.lottery_data["chat_settings"] = {}
        
        if peer_id_str not in self.lottery_data["chat_settings"]:
            # Используем глобальные настройки как значения по умолчанию
            global_settings = self.lottery_data.get("global_settings", {})
            rp_mode = global_settings.get("default_rp_mode", False)
            
            self.lottery_data["chat_settings"][peer_id_str] = {
                "rp_mode": rp_mode,
                "winner_count": global_settings.get("default_winner_count", 3)
            }
            
            # Цену билета устанавливаем только если РП-режим включен
            if rp_mode:
                self.lottery_data["chat_settings"][peer_id_str]["ticket_price"] = global_settings.get("default_ticket_price", 100)
        
        return self.lottery_data["chat_settings"][peer_id_str]
    
    def create_lottery(self, peer_id, admin_id):
        """Создать новую лотерею"""
        peer_id_str = str(peer_id)
        
        if peer_id_str in self.lottery_data["chats"] and self.lottery_data["chats"][peer_id_str].get("active"):
            return "❌ В беседе уже есть активная лотерея! Завершите её командой 'лотерея стоп'."
        
        # Получаем настройки для данной беседы
        chat_settings = self._get_chat_settings(peer_id)
        
        lottery_data = {
            "active": True,
            "tickets": {},
            "prize_pool": 0,
            "admin": admin_id,
            "rp_mode": chat_settings["rp_mode"],
            "winner_count": chat_settings["winner_count"],
            "created_at": datetime.now().isoformat()
        }
        
        # Цену билета устанавливаем только если РП-режим включен
        if chat_settings["rp_mode"]:
            lottery_data["ticket_price"] = chat_settings.get("ticket_price", 100)
        
        self.lottery_data["chats"][peer_id_str] = lottery_data
        
        self._save_lottery_data()
        admin_name = get_user_name(admin_id)
        return f"🎟️ Лотерея создана!\n👑 Администратор: {admin_name}\n\n📝 Команды:\n• лотерея билет @пользователь [количество] - выдать билеты\n• лотерея мои - посмотреть свои билеты\n• лотерея список - список всех участников\n• лотерея розыгрыш - провести розыгрыш\n• лотерея стоп - завершить лотерею"
    
    def give_tickets(self, peer_id, admin_id, target_user_id, count):
        """Выдать билеты пользователю"""
        peer_id_str = str(peer_id)
        
        if peer_id_str not in self.lottery_data["chats"] or not self.lottery_data["chats"][peer_id_str].get("active"):
            return "❌ В беседе нет активной лотереи. Создайте её командой 'лотерея'."
        
        lottery = self.lottery_data["chats"][peer_id_str]
        
        if lottery["admin"] != admin_id:
            return "❌ Только администратор лотереи может выдавать билеты!"
        
        if count < 1 or count > 10:
            return "❌ Можно выдать от 1 до 10 билетов за раз."
        
        # Генерируем билеты с уникальными номерами
        user_id_str = str(target_user_id)
        if user_id_str not in lottery["tickets"]:
            lottery["tickets"][user_id_str] = []
        
        new_tickets = []
        for _ in range(count):
            # Генерируем уникальный номер билета (6-значный)
            while True:
                ticket_number = random.randint(100000, 999999)
                # Проверяем, что номер не используется в этой лотерее
                used_numbers = []
                for tickets in lottery["tickets"].values():
                    used_numbers.extend(tickets)
                if ticket_number not in used_numbers:
                    break
            
            new_tickets.append(ticket_number)
            lottery["tickets"][user_id_str].append(ticket_number)
        
        # Обновляем призовой фонд (только если РП-режим включен)
        rp_mode = lottery.get("rp_mode", False)
        if rp_mode:
            ticket_price = lottery.get("ticket_price", 100)
            lottery["prize_pool"] += count * ticket_price
        
        self._save_lottery_data()
        
        target_name = get_user_name(target_user_id)
        admin_name = get_user_name(admin_id)
        
        tickets_text = "\n".join([f"🎟️ {ticket}" for ticket in new_tickets])
        
        # Формируем ответ в зависимости от режима
        if rp_mode:
            currency = "золотых" if lottery.get("ticket_price", 100) != 1 else "золотой"
            return f"✅ {admin_name} выдал {count} билет(ов) пользователю {target_name}!\n\n{tickets_text}\n\n💰 Призовой фонд: {lottery['prize_pool']} {currency}"
        else:
            return f"✅ {admin_name} выдал {count} билет(ов) пользователю {target_name}!\n\n{tickets_text}"
    
    def get_my_tickets(self, peer_id, user_id):
        """Посмотреть свои билеты"""
        peer_id_str = str(peer_id)
        
        if peer_id_str not in self.lottery_data["chats"] or not self.lottery_data["chats"][peer_id_str].get("active"):
            return "❌ В беседе нет активной лотереи."
        
        lottery = self.lottery_data["chats"][peer_id_str]
        user_id_str = str(user_id)
        
        if user_id_str not in lottery["tickets"] or not lottery["tickets"][user_id_str]:
            return "❌ У вас нет билетов в этой лотерее."
        
        user_name = get_user_name(user_id)
        tickets = lottery["tickets"][user_id_str]
        tickets_text = "\n".join([f"🎟️ {ticket}" for ticket in tickets])
        
        # Формируем ответ в зависимости от режима
        rp_mode = lottery.get("rp_mode", False)
        if rp_mode:
            currency = "золотых" if lottery.get("prize_pool", 0) != 1 else "золотой"
            return f"🎟️ Билеты пользователя {user_name}:\n\n{tickets_text}\n\n📊 Всего билетов: {len(tickets)}\n💰 Призовой фонд: {lottery['prize_pool']} {currency}"
        else:
            return f"🎟️ Билеты пользователя {user_name}:\n\n{tickets_text}\n\n📊 Всего билетов: {len(tickets)}"
    
    def get_participants_list(self, peer_id):
        """Получить список всех участников"""
        peer_id_str = str(peer_id)
        
        if peer_id_str not in self.lottery_data["chats"] or not self.lottery_data["chats"][peer_id_str].get("active"):
            return "❌ В беседе нет активной лотереи."
        
        lottery = self.lottery_data["chats"][peer_id_str]
        
        if not lottery["tickets"]:
            return "❌ В лотерее пока нет участников."
        
        response = "🎟️ УЧАСТНИКИ ЛОТЕРЕИ:\n\n"
        total_tickets = 0
        
        # Сортируем участников по количеству билетов (убывание)
        participants = []
        for user_id_str, tickets in lottery["tickets"].items():
            if tickets:  # Только если есть билеты
                user_id = int(user_id_str)
                user_name = get_user_name(user_id)
                participants.append((user_name, len(tickets), user_id))
                total_tickets += len(tickets)
        
        participants.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, ticket_count, user_id) in enumerate(participants, 1):
            chance = (ticket_count / total_tickets) * 100 if total_tickets > 0 else 0
            response += f"{i}. {name} - {ticket_count} билет(ов) ({chance:.1f}%)\n"
        
        admin_name = get_user_name(lottery["admin"])
        
        # Формируем ответ в зависимости от режима
        rp_mode = lottery.get("rp_mode", False)
        if rp_mode:
            currency = "золотых" if lottery.get("prize_pool", 0) != 1 else "золотой"
            response += f"\n📊 Всего билетов: {total_tickets}\n💰 Призовой фонд: {lottery['prize_pool']} {currency}\n👑 Администратор: {admin_name}"
        else:
            response += f"\n📊 Всего билетов: {total_tickets}\n👑 Администратор: {admin_name}"
        
        return response
    
    def conduct_draw(self, peer_id, admin_id):
        """Провести розыгрыш лотереи"""
        peer_id_str = str(peer_id)
        
        if peer_id_str not in self.lottery_data["chats"] or not self.lottery_data["chats"][peer_id_str].get("active"):
            return "❌ В беседе нет активной лотереи."
        
        lottery = self.lottery_data["chats"][peer_id_str]
        
        if lottery["admin"] != admin_id:
            return "❌ Только администратор лотереи может провести розыгрыш!"
        
        if not lottery["tickets"] or all(not tickets for tickets in lottery["tickets"].values()):
            return "❌ В лотерее нет участников с билетами!"
        
        # Собираем все билеты
        all_tickets = []
        for user_id_str, tickets in lottery["tickets"].items():
            for ticket in tickets:
                all_tickets.append((ticket, int(user_id_str)))
        
        if len(all_tickets) < 1:
            return "❌ В лотерее недостаточно билетов!"
        
        # Получаем количество победителей из настроек лотереи
        winner_count = lottery.get("winner_count", 3)
        
        # Определяем количество призовых мест (не больше количества уникальных участников)
        unique_participants = len(set(lottery["tickets"].keys()))
        prize_places = min(winner_count, unique_participants)
        
        # Розыгрыш
        winners = []
        remaining_tickets = all_tickets.copy()
        
        for place in range(1, prize_places + 1):
            if not remaining_tickets:
                break
            
            # Выбираем случайный билет
            winning_ticket, winner_id = random.choice(remaining_tickets)
            winners.append((place, winning_ticket, winner_id))
            
            # Убираем все билеты этого пользователя (чтобы не выиграл дважды)
            remaining_tickets = [(t, u) for t, u in remaining_tickets if u != winner_id]
        
        # Рассчитываем призы в зависимости от количества мест
        prize_pool = lottery["prize_pool"]
        
        # Формируем распределение призов
        if prize_places == 1:
            prize_distribution = {1: 1.0}  # 100%
        elif prize_places == 2:
            prize_distribution = {1: 0.7, 2: 0.3}  # 70%, 30%
        elif prize_places == 3:
            prize_distribution = {1: 0.6, 2: 0.3, 3: 0.1}  # 60%, 30%, 10%
        else:
            # Для 4+ мест равномерно распределяем призы с уменьшением
            prize_distribution = {}
            # Первое место получает 40%
            prize_distribution[1] = 0.4
            # Остальные места делят оставшиеся 60%
            remaining_percent = 0.6
            for i in range(2, prize_places + 1):
                prize_distribution[i] = remaining_percent / (prize_places - 1)
        
        response = "🎉 РЕЗУЛЬТАТЫ РОЗЫГРЫША ЛОТЕРЕИ! 🎉\n\n"
        
        # Проверяем РП-режим
        rp_mode = lottery.get("rp_mode", False)
        
        for place, ticket, winner_id in winners:
            winner_name = get_user_name(winner_id)
            
            if place == 1:
                emoji = "🥇"
                place_text = "ГЛАВНЫЙ ПРИЗ"
            elif place == 2:
                emoji = "🥈"
                place_text = "ВТОРОЕ МЕСТО"
            elif place == 3:
                emoji = "🥉"
                place_text = "ТРЕТЬЕ МЕСТО"
            else:
                emoji = "🏅"
                place_text = f"{place}-Е МЕСТО"
            
            response += f"{emoji} {place_text}:\n"
            response += f"🎟️ Билет: {ticket}\n"
            response += f"👤 Победитель: {winner_name}\n"
            
            # Показываем призы только в РП-режиме
            if rp_mode:
                prize = int(prize_pool * prize_distribution.get(place, 0))
                currency = "золотых" if prize != 1 else "золотой"
                response += f"💰 Приз: {prize} {currency}\n"
            
            response += "\n"
        
        response += f"🎟️ Всего участвовало билетов: {len(all_tickets)}\n"
        
        # Показываем призовой фонд только в РП-режиме
        if rp_mode:
            currency = "золотых" if prize_pool != 1 else "золотой"
            response += f"💰 Общий призовой фонд: {prize_pool} {currency}"
        
        # Завершаем лотерею
        lottery["active"] = False
        lottery["completed_at"] = datetime.now().isoformat()
        lottery["winners"] = winners
        
        self._save_lottery_data()
        
        return response
    
    def stop_lottery(self, peer_id, admin_id):
        """Остановить лотерею"""
        peer_id_str = str(peer_id)
        
        if peer_id_str not in self.lottery_data["chats"] or not self.lottery_data["chats"][peer_id_str].get("active"):
            return "❌ В беседе нет активной лотереи."
        
        lottery = self.lottery_data["chats"][peer_id_str]
        
        if lottery["admin"] != admin_id:
            return "❌ Только администратор лотереи может остановить её!"
        
        # Подсчитываем статистику
        total_tickets = sum(len(tickets) for tickets in lottery["tickets"].values())
        participants_count = len([tickets for tickets in lottery["tickets"].values() if tickets])
        
        lottery["active"] = False
        lottery["stopped_at"] = datetime.now().isoformat()
        
        self._save_lottery_data()
        
        admin_name = get_user_name(admin_id)
        
        # Формируем ответ в зависимости от режима
        rp_mode = lottery.get("rp_mode", False)
        if rp_mode:
            currency = "золотых" if lottery['prize_pool'] != 1 else "золотой"
            return f"🛑 Лотерея остановлена администратором {admin_name}!\n\n📊 Статистика:\n• Участников: {participants_count}\n• Билетов выдано: {total_tickets}\n• Призовой фонд: {lottery['prize_pool']} {currency}\n\n💡 Для проведения нового розыгрыша создайте новую лотерею командой 'лотерея'."
        else:
            return f"🛑 Лотерея остановлена администратором {admin_name}!\n\n📊 Статистика:\n• Участников: {participants_count}\n• Билетов выдано: {total_tickets}\n\n💡 Для проведения нового розыгрыша создайте новую лотерею командой 'лотерея'."
    
    def enable_rp_mode(self, peer_id, creator_id):
        """Включить РП-режим лотереи для конкретной беседы (только создатель)"""
        peer_id_str = str(peer_id)
        
        # Проверяем, что нет активной лотереи
        if peer_id_str in self.lottery_data["chats"] and self.lottery_data["chats"][peer_id_str].get("active"):
            return "❌ Нельзя изменить режим во время активной лотереи! Завершите её командой 'лотерея стоп'."
        
        # Инициализируем настройки для беседы если их нет
        if "chat_settings" not in self.lottery_data:
            self.lottery_data["chat_settings"] = {}
        
        if peer_id_str not in self.lottery_data["chat_settings"]:
            self.lottery_data["chat_settings"][peer_id_str] = {
                "rp_mode": False,
                "winner_count": 3
            }
        
        self.lottery_data["chat_settings"][peer_id_str]["rp_mode"] = True
        # При включении РП-режима устанавливаем цену билета по умолчанию
        if "ticket_price" not in self.lottery_data["chat_settings"][peer_id_str]:
            self.lottery_data["chat_settings"][peer_id_str]["ticket_price"] = 100
        
        self._save_lottery_data()
        
        creator_name = get_user_name(creator_id)
        return f"✅ РП-режим лотереи включен администратором {creator_name} для этой беседы!\n\n🎯 ИЗМЕНЕНИЯ:\n• Призовой фонд теперь рассчитывается в золотых\n• Можно настроить цену билета командой 'лотерея цена [число]'\n• По умолчанию: 1 билет = 100 золотых\n• Настройки действуют только в этой беседе\n\n💡 Для отключения используйте 'лотерея рп выкл'"
    
    def disable_rp_mode(self, peer_id, creator_id):
        """Выключить РП-режим лотереи для конкретной беседы (только создатель)"""
        peer_id_str = str(peer_id)
        
        # Проверяем, что нет активной лотереи
        if peer_id_str in self.lottery_data["chats"] and self.lottery_data["chats"][peer_id_str].get("active"):
            return "❌ Нельзя изменить режим во время активной лотереи! Завершите её командой 'лотерея стоп'."
        
        # Инициализируем настройки для беседы если их нет
        if "chat_settings" not in self.lottery_data:
            self.lottery_data["chat_settings"] = {}
        
        if peer_id_str not in self.lottery_data["chat_settings"]:
            self.lottery_data["chat_settings"][peer_id_str] = {
                "rp_mode": False,
                "winner_count": 3
            }
        
        self.lottery_data["chat_settings"][peer_id_str]["rp_mode"] = False
        # При выключении РП-режима удаляем цену билета, так как она не нужна
        if "ticket_price" in self.lottery_data["chat_settings"][peer_id_str]:
            del self.lottery_data["chat_settings"][peer_id_str]["ticket_price"]
        
        self._save_lottery_data()
        
        creator_name = get_user_name(creator_id)
        return f"✅ РП-режим лотереи выключен администратором {creator_name} для этой беседы!\n\n🎯 ИЗМЕНЕНИЯ:\n• Призовой фонд отключен\n• Организаторы сами назначают призы вне бота\n• Лотерея работает только для определения победителей\n• Настройки действуют только в этой беседе\n\n💡 Для включения используйте 'лотерея рп вкл'"
    
    def set_winner_count(self, peer_id, creator_id, count):
        """Установить количество победителей для конкретной беседы (только создатель и админы)"""
        peer_id_str = str(peer_id)
        
        # Проверяем корректность количества
        if count < 1 or count > 10:
            return "❌ Количество победителей должно быть от 1 до 10!"
        
        # Проверяем, что нет активной лотереи
        if peer_id_str in self.lottery_data["chats"] and self.lottery_data["chats"][peer_id_str].get("active"):
            return "❌ Нельзя изменить количество победителей во время активной лотереи! Завершите её командой 'лотерея стоп'."
        
        # Инициализируем настройки для беседы если их нет
        if "chat_settings" not in self.lottery_data:
            self.lottery_data["chat_settings"] = {}
        
        if peer_id_str not in self.lottery_data["chat_settings"]:
            self.lottery_data["chat_settings"][peer_id_str] = {
                "rp_mode": False,
                "winner_count": 3
            }
        
        self.lottery_data["chat_settings"][peer_id_str]["winner_count"] = count
        self._save_lottery_data()
        
        creator_name = get_user_name(creator_id)
        return f"✅ Количество победителей изменено администратором {creator_name} для этой беседы!\n\n🏆 Новые настройки:\n• Количество мест: {count}\n• Следующая лотерея будет иметь {count} призовых мест\n• Настройки действуют только в этой беседе\n\n💡 Изменения вступят в силу для новых лотерей"
    
    def set_ticket_price(self, peer_id, creator_id, price):
        """Установить цену билета в золотых для конкретной беседы (только создатель)"""
        peer_id_str = str(peer_id)
        
        # Проверяем, что нет активной лотереи
        if peer_id_str in self.lottery_data["chats"] and self.lottery_data["chats"][peer_id_str].get("active"):
            return "❌ Нельзя изменить цену билета во время активной лотереи! Завершите её командой 'лотерея стоп'."
        
        # Получаем настройки беседы
        chat_settings = self._get_chat_settings(peer_id)
        
        # Проверяем, что РП-режим включен
        if not chat_settings.get("rp_mode", False):
            return "❌ Цену билета можно изменить только при включенном РП-режиме! Включите его командой 'лотерея рп вкл'."
        
        if price < 1 or price > 10000:
            return "❌ Цена билета должна быть от 1 до 10000 золотых!"
        
        # Инициализируем настройки для беседы если их нет
        if "chat_settings" not in self.lottery_data:
            self.lottery_data["chat_settings"] = {}
        
        if peer_id_str not in self.lottery_data["chat_settings"]:
            self.lottery_data["chat_settings"][peer_id_str] = {
                "rp_mode": True,  # Мы уже проверили, что РП-режим включен
                "winner_count": 3
            }
        
        self.lottery_data["chat_settings"][peer_id_str]["ticket_price"] = price
        self._save_lottery_data()
        
        creator_name = get_user_name(creator_id)
        rp_status = "включен" if self.lottery_data["chat_settings"][peer_id_str]["rp_mode"] else "выключен"
        return f"✅ Цена билета установлена администратором {creator_name} для этой беседы!\n\n💰 Новая цена: {price} золотых за билет\n🎯 РП-режим: {rp_status}\n• Настройки действуют только в этой беседе\n\n💡 Изменения применятся к новым лотереям."
