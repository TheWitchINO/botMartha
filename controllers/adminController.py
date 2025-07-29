import json
import os
from controllers.messageController import get_user_name

class AdminController:
    def __init__(self):
        self.data_file = "data/admin_data.json"
        self.admin_data = self._load_admin_data()
        
    def _load_admin_data(self):
        """Загрузить данные администраторов и модераторов"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Структура по умолчанию
        return {
            "chats": {}  # {peer_id: {"creator": user_id, "admins": [], "moderators": []}}
        }
    
    def _save_admin_data(self):
        """Сохранить данные администраторов и модераторов"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.admin_data, f, ensure_ascii=False, indent=2)
    
    def set_creator(self, peer_id, user_id):
        """Назначить создателя беседы (только если его еще нет)"""
        peer_id_str = str(peer_id)
        
        if peer_id_str not in self.admin_data["chats"]:
            self.admin_data["chats"][peer_id_str] = {"creator": None, "admins": [], "moderators": []}
        
        if self.admin_data["chats"][peer_id_str].get("creator") is not None:
            creator_name = get_user_name(self.admin_data["chats"][peer_id_str]["creator"])
            return f"❌ В беседе уже есть создатель: {creator_name}!"
        
        self.admin_data["chats"][peer_id_str]["creator"] = user_id
        # Если пользователь был админом или модератором, убираем его оттуда
        if user_id in self.admin_data["chats"][peer_id_str]["admins"]:
            self.admin_data["chats"][peer_id_str]["admins"].remove(user_id)
        if user_id in self.admin_data["chats"][peer_id_str]["moderators"]:
            self.admin_data["chats"][peer_id_str]["moderators"].remove(user_id)
        
        self._save_admin_data()
        user_name = get_user_name(user_id)
        return f"👑 {user_name} назначен создателем беседы!"
    
    def transfer_creator(self, peer_id, current_creator_id, new_creator_id):
        """Передать права создателя другому пользователю"""
        peer_id_str = str(peer_id)
        
        # Проверяем, что текущий пользователь действительно создатель
        if not self.is_creator(peer_id, current_creator_id):
            return "❌ Только создатель может передать свои права!"
        
        # Проверяем, что не пытаемся передать права самому себе
        if current_creator_id == new_creator_id:
            return "❌ Вы не можете передать права самому себе!"
        
        if peer_id_str not in self.admin_data["chats"]:
            return "❌ Ошибка: данные беседы не найдены."
        
        chat_data = self.admin_data["chats"][peer_id_str]
        
        # Передаем права
        chat_data["creator"] = new_creator_id
        
        # Убираем нового создателя из админов/модераторов, если он там был
        if new_creator_id in chat_data["admins"]:
            chat_data["admins"].remove(new_creator_id)
        if new_creator_id in chat_data["moderators"]:
            chat_data["moderators"].remove(new_creator_id)
        
        # Бывшего создателя делаем админом
        if current_creator_id not in chat_data["admins"]:
            chat_data["admins"].append(current_creator_id)
        
        self._save_admin_data()
        
        old_creator_name = get_user_name(current_creator_id)
        new_creator_name = get_user_name(new_creator_id)
        return f"👑 {old_creator_name} передал права создателя пользователю {new_creator_name}!\n🔻 {old_creator_name} теперь администратор."
    
    def is_creator(self, peer_id, user_id):
        """Проверить, является ли пользователь создателем беседы"""
        peer_id_str = str(peer_id)
        if peer_id_str in self.admin_data["chats"]:
            return self.admin_data["chats"][peer_id_str].get("creator") == user_id
        return False
    
    def is_admin(self, peer_id, user_id):
        """Проверить, является ли пользователь администратором в беседе"""
        if self.is_creator(peer_id, user_id):
            return True
        
        peer_id_str = str(peer_id)
        if peer_id_str in self.admin_data["chats"]:
            return user_id in self.admin_data["chats"][peer_id_str].get("admins", [])
        return False
    
    def is_moderator(self, peer_id, user_id):
        """Проверить, является ли пользователь модератором в беседе"""
        if self.is_admin(peer_id, user_id):
            return True
        
        peer_id_str = str(peer_id)
        if peer_id_str in self.admin_data["chats"]:
            return user_id in self.admin_data["chats"][peer_id_str].get("moderators", [])
        return False
    
    def promote_user(self, peer_id, user_id, target_user_id):
        """Повысить пользователя в должности"""
        peer_id_str = str(peer_id)
        
        # Инициализируем данные беседы если их нет
        if peer_id_str not in self.admin_data["chats"]:
            self.admin_data["chats"][peer_id_str] = {"creator": None, "admins": [], "moderators": []}
        
        chat_data = self.admin_data["chats"][peer_id_str]
        
        # Определяем текущую роль цели
        if target_user_id == chat_data.get("creator"):
            return "❌ Создателя нельзя повысить!"
        elif target_user_id in chat_data["admins"]:
            return "❌ Администратора нельзя повысить до создателя!"
        elif target_user_id in chat_data["moderators"]:
            # Повышение модератора до админа (может только создатель или админ)
            if not self.is_admin(peer_id, user_id):
                return "❌ Только администраторы и создатель могут повышать модераторов!"
            
            chat_data["moderators"].remove(target_user_id)
            chat_data["admins"].append(target_user_id)
            self._save_admin_data()
            
            target_name = get_user_name(target_user_id)
            promoter_name = get_user_name(user_id)
            return f"⬆️ {target_name} повышен до администратора пользователем {promoter_name}!"
        else:
            # Повышение обычного пользователя до модератора (может только модератор и выше)
            if not self.is_moderator(peer_id, user_id):
                return "❌ Только модераторы и выше могут повышать пользователей!"
            
            chat_data["moderators"].append(target_user_id)
            self._save_admin_data()
            
            target_name = get_user_name(target_user_id)
            promoter_name = get_user_name(user_id)
            return f"⬆️ {target_name} повышен до модератора пользователем {promoter_name}!"
    
    def demote_user(self, peer_id, user_id, target_user_id):
        """Понизить пользователя в должности"""
        peer_id_str = str(peer_id)
        
        if peer_id_str not in self.admin_data["chats"]:
            return "❌ В этой беседе нет администрации."
        
        chat_data = self.admin_data["chats"][peer_id_str]
        
        # Определяем текущую роль цели
        if target_user_id == chat_data.get("creator"):
            return "❌ Создателя нельзя понизить!"
        elif target_user_id in chat_data["admins"]:
            # Понижение админа до модератора (может только создатель)
            if not self.is_creator(peer_id, user_id):
                return "❌ Только создатель может понижать администраторов!"
            
            chat_data["admins"].remove(target_user_id)
            chat_data["moderators"].append(target_user_id)
            self._save_admin_data()
            
            target_name = get_user_name(target_user_id)
            demoter_name = get_user_name(user_id)
            return f"⬇️ {target_name} понижен до модератора пользователем {demoter_name}!"
        elif target_user_id in chat_data["moderators"]:
            # Понижение модератора до обычного пользователя (может только админ и выше)
            if not self.is_admin(peer_id, user_id):
                return "❌ Только администраторы и создатель могут понижать модераторов!"
            
            chat_data["moderators"].remove(target_user_id)
            self._save_admin_data()
            
            target_name = get_user_name(target_user_id)
            demoter_name = get_user_name(user_id)
            return f"⬇️ {target_name} понижен до обычного пользователя пользователем {demoter_name}!"
        else:
            return f"❌ {get_user_name(target_user_id)} не имеет никаких должностей для понижения."
    
    def get_chat_staff(self, peer_id):
        """Получить список администраторов и модераторов беседы"""
        peer_id_str = str(peer_id)
        
        response = "👑 АДМИНИСТРАЦИЯ БЕСЕДЫ:\n\n"
        
        # Создатель
        if peer_id_str in self.admin_data["chats"]:
            chat_data = self.admin_data["chats"][peer_id_str]
            
            if chat_data.get("creator"):
                creator_name = get_user_name(chat_data["creator"])
                response += f"🔥 Создатель: {creator_name}\n\n"
            
            # Админы беседы
            if chat_data.get("admins"):
                response += "👑 Администраторы беседы:\n"
                for admin_id in chat_data["admins"]:
                    response += f"• {get_user_name(admin_id)}\n"
                response += "\n"
            
            # Модераторы
            if chat_data.get("moderators"):
                response += "⚖️ Модераторы беседы:\n"
                for mod_id in chat_data["moderators"]:
                    response += f"• {get_user_name(mod_id)}\n"
                response += "\n"
        
        if response == "👑 АДМИНИСТРАЦИЯ БЕСЕДЫ:\n\n":
            response = "❌ В этой беседе нет назначенных администраторов или модераторов."
        
        return response.strip()
    
    def get_user_permissions(self, peer_id, user_id):
        """Получить информацию о правах пользователя"""
        user_name = get_user_name(user_id)
        
        if self.is_creator(peer_id, user_id):
            return (
                f"� {user_name} - Создатель беседы\n\n"
                "💪 ВАШИ ВОЗМОЖНОСТИ:\n"
                "• Абсолютная власть!\n"
                "• Исключение пользователей из беседы\n"
                "• Создание и управление лотереями\n"
                "• Принудительное завершение игр\n"
                "• Полный доступ ко всем функциям бота"
            )
        elif self.is_admin(peer_id, user_id):
            return (
                f"� {user_name} - Администратор беседы\n\n"
                "💪 ВАШИ ВОЗМОЖНОСТИ:\n"
                "• Назначение и снятие модераторов\n"
                "• Исключение пользователей из беседы\n"
                "• Создание и управление лотереями\n"
                "• Принудительное завершение игр\n"
            )
        elif self.is_moderator(peer_id, user_id):
            return (
                f"⚖️ {user_name} - Модератор беседы\n\n"
                "💪 ВАШИ ВОЗМОЖНОСТИ:\n"
                "• Повышение пользователей до модераторов\n"
                "• Исключение пользователей из беседы\n"
                "• Принудительное завершение игр\n"
                "• Базовые модераторские права"
            )
        else:
            return (
                f"👤 {user_name} - Обычный пользователь\n\n"
                "💪 ВАШИ ВОЗМОЖНОСТИ:\n"
                "• Стандартные пользовательские функции"
            )
    
    def get_admin_commands_help(self, peer_id, user_id):
        """Получить справку по админским командам в зависимости от уровня доступа"""
        if self.is_creator(peer_id, user_id):
            return (
                "� КОМАНДЫ СОЗДАТЕЛЯ:\n\n"
                "• Админка - список администрации беседы\n"
                "• Мои права - проверить свои права\n"
                "• Права (ответ) - проверить права пользователя\n"
                "• Повысить (ответ) - повысить пользователя в должности\n"
                "• Понизить (ответ) - понизить пользователя в должности\n"
                "• Перелдать власть (ответ) - передать права создателя пользователю\n"
                "• Кик (ответ) - исключить пользователя из беседы\n"
                "• Лотерея - создать лотерею и управлять ею\n"
                "• Стоп игры - принудительно завершить все игры\n"
            )
        elif self.is_admin(peer_id, user_id):
            return (
                "� КОМАНДЫ АДМИНИСТРАТОРА:\n\n"
                "• Админка - список администрации беседы\n"
                "• Мои права - проверить свои права\n"
                "• Права (ответ) - проверить права пользователя\n"
                "• Повысить (ответ) - повысить пользователя до модератора\n"
                "• Понизить (ответ) - понизить модератора до пользователя\n"
                "• Кик (ответ) - исключить пользователя из беседы\n"
                "• Лотерея - создать лотерею и управлять ею\n"
                "• Стоп игры - принудительно завершить все игры\n"
            )
        elif self.is_moderator(peer_id, user_id):
            return (
                "⚖️ КОМАНДЫ МОДЕРАТОРА:\n\n"
                "• Админка - список администрации беседы\n"
                "• Мои права - проверить свои права\n"
                "• Права (ответ) - проверить права пользователя\n"
                "• Повысить (ответ) - повысить пользователя до модератора\n"
                "• Кик (ответ) - исключить пользователя из беседы\n"
                "• Стоп игры - принудительно завершить все игры\n"
            )
        else:
            return "❌ У вас нет прав администратора или модератора."
    
    def kick_user(self, peer_id, user_id, target_user_id, vk_api):
        """Кикнуть пользователя из беседы"""
        if not self.is_moderator(peer_id, user_id):
            return "❌ У вас нет прав для исключения пользователей."
        
        if target_user_id == user_id:
            return "❌ Вы не можете исключить самого себя."
        
        # Проверяем, что не пытаемся кикнуть вышестоящего
        if self.is_creator(peer_id, target_user_id):
            return "❌ Нельзя исключить создателя беседы."
        
        if self.is_admin(peer_id, target_user_id) and not self.is_creator(peer_id, user_id):
            return "❌ Только создатель может исключить администратора."
        
        if self.is_moderator(peer_id, target_user_id) and not self.is_admin(peer_id, user_id):
            return "❌ Только администратор или создатель может исключить модератора."
        
        try:
            # VK API для исключения пользователя
            vk_api.messages.removeChatUser(
                chat_id=peer_id - 2000000000,
                member_id=target_user_id
            )
            
            target_name = get_user_name(target_user_id)
            kicker_name = get_user_name(user_id)
            return f"👋 {target_name} исключен из беседы пользователем {kicker_name}."
        except Exception as e:
            return f"❌ Ошибка при исключении пользователя: {str(e)}"
