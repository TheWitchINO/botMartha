import random
import time
from controllers.messageController import get_user_name

class BingoController:
    def __init__(self):
        self.games = {}  # {peer_id: {host_id: id, players: {user_id: card}, drawn_numbers: [], current_game: bool}}
        self.pending_games = {}  # {peer_id: {host_id: id, players: [], timestamp: float}}

    def start_game(self, peer_id, host_id):
        """Создание лобби для игры в лото"""
        if peer_id in self.games:
            return "Игра в лото уже идет в этой беседе!"
        
        if peer_id in self.pending_games:
            return "Набор игроков уже идет! Напишите 'лото вступить', чтобы присоединиться."
        
        self.pending_games[peer_id] = {
            "host_id": host_id,
            "players": [host_id],
            "timestamp": time.time()
        }
        
        host_name = get_user_name(host_id)
        return f"🎲 {host_name} начинает набор игроков в лото!\n\n" \
               f"📝 Для участия напишите 'лото вступить'\n" \
               f"🎯 Для начала игры ведущий должен написать 'лото начать'\n" \
               f"⏰ У вас есть 5 минут для набора игроков"

    def join_game(self, peer_id, user_id):
        """Присоединение к лобби игры"""
        if peer_id not in self.pending_games:
            return "❌ Сейчас нет активного набора в лото."
        
        # Проверяем, не истекло ли время
        if time.time() - self.pending_games[peer_id]["timestamp"] > 300:  # 5 минут
            del self.pending_games[peer_id]
            return "⏰ Время набора игроков истекло."

        if user_id in self.pending_games[peer_id]["players"]:
            return "✅ Вы уже присоединились к игре."

        self.pending_games[peer_id]["players"].append(user_id)
        players_list = [get_user_name(pid) for pid in self.pending_games[peer_id]["players"]]
        
        return f"🎉 {get_user_name(user_id)} присоединился к игре в лото!\n\n" \
               f"👥 Текущие игроки ({len(players_list)}): {', '.join(players_list)}\n" \
               f"🎯 Ведущий может написать 'лото начать' для начала игры"

    def start_bingo(self, peer_id, user_id):
        """Запуск игры в лото (только ведущий может запустить)"""
        if peer_id not in self.pending_games:
            return "❌ Нет активного лобби для начала игры."
            
        if self.pending_games[peer_id]["host_id"] != user_id:
            host_name = get_user_name(self.pending_games[peer_id]["host_id"])
            return f"❌ Только ведущий ({host_name}) может начать игру!"
            
        if len(self.pending_games[peer_id]["players"]) < 2:
            return "❌ Нужно минимум 2 игрока для начала игры в лото."

        # Создаем карточки для игроков
        players = self.pending_games[peer_id]["players"]
        player_cards = {}
        
        for player_id in players:
            player_cards[player_id] = self._generate_bingo_card()
        
        # Создаем игру
        self.games[peer_id] = {
            "host_id": self.pending_games[peer_id]["host_id"],
            "players": player_cards,
            "drawn_numbers": [],
            "current_game": True,
            "numbers_left": list(range(1, 91)),  # Числа от 1 до 90
            "excluded_players": []  # Исключенные за читерство игроки
        }
        
        # Удаляем лобби
        del self.pending_games[peer_id]
        
        # Формируем сообщение с карточками игроков
        response = "🎲 ИГРА В ЛОТО НАЧАЛАСЬ! 🎲\n\n"
        
        for player_id, card in player_cards.items():
            player_name = get_user_name(player_id)
            response += f"📋 Карточка {player_name}:\n"
            response += self._format_card(card) + "\n\n"
        
        response += "🎯 Ведущий может написать 'лото число', чтобы вытянуть следующий номер!\n"
        response += "✅ Игроки отмечают числа на своих карточках"
        
        return response

    def draw_number(self, peer_id, user_id):
        """Вытягивание следующего числа (только ведущий)"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
            
        if not self.games[peer_id]["current_game"]:
            return "❌ Игра в лото уже завершена."
            
        if self.games[peer_id]["host_id"] != user_id:
            host_name = get_user_name(self.games[peer_id]["host_id"])
            return f"❌ Только ведущий ({host_name}) может вытягивать числа!"
        
        if not self.games[peer_id]["numbers_left"]:
            return "🎉 Все числа уже вытянуты!"
        
        # Вытягиваем случайное число
        drawn_number = random.choice(self.games[peer_id]["numbers_left"])
        self.games[peer_id]["numbers_left"].remove(drawn_number)
        self.games[peer_id]["drawn_numbers"].append(drawn_number)
        
        response = f"🎲 Выпало число: {drawn_number}\n\n"
        response += f"📊 Вытянуто чисел: {len(self.games[peer_id]['drawn_numbers'])}/90\n"
        
        # Проверяем, есть ли у кого-то бинго (заполненная горизонтальная линия)
        winners = self._check_for_line_winners(peer_id)
        if winners:
            response += "\n🎉 БИНГО! ЗАПОЛНЕНА ЛИНИЯ! 🎉\n"
            
            # Получаем результаты всех игроков
            results = self._get_game_results(peer_id)
            
            # Показываем победителей (1 место)
            for winner_id in winners:
                winner_name = get_user_name(winner_id)
                response += f"🥇 1-е место: {winner_name} (заполнил линию!)\n"
            
            # Показываем 2-е и 3-е места по количеству зачеркнутых чисел
            places = self._determine_places(results, winners)
            
            if places.get(2):
                response += f"🥈 2-е место: {', '.join([get_user_name(pid) for pid in places[2]])} ({results[places[2][0]]['marked_count']} чисел)\n"
            
            if places.get(3):
                response += f"🥉 3-е место: {', '.join([get_user_name(pid) for pid in places[3]])} ({results[places[3][0]]['marked_count']} чисел)\n"
            
            self.games[peer_id]["current_game"] = False
            response += "\n🎮 Игра завершена!"
        else:
            response += "\n🎯 Ведущий может написать 'лото число' для следующего числа"
        
        return response

    def check_card(self, peer_id, user_id):
        """Показать карточку игрока с отмеченными числами"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
            
        if user_id not in self.games[peer_id]["players"]:
            return "❌ Вы не участвуете в этой игре."
        
        if user_id in self.games[peer_id]["excluded_players"]:
            return "🚨 Вы исключены из игры за читерство! Больше не можете участвовать."
        
        card = self.games[peer_id]["players"][user_id]
        drawn_numbers = self.games[peer_id]["drawn_numbers"]
        
        response = f"📋 Ваша карточка:\n"
        response += self._format_card_with_marks(card, drawn_numbers)
        
        # Проверяем, сколько чисел отмечено
        marked_count = sum(1 for row in card for num in row if num in drawn_numbers and num != 0)
        total_count = sum(1 for row in card for num in row if num != 0)
        
        response += f"\n✅ Отмечено: {marked_count}/{total_count}"
        
        # Анализируем линии
        line_analysis = self._analyze_lines(card, drawn_numbers)
        if line_analysis:
            response += f"\n\n📊 Анализ линий:\n{line_analysis}"
        
        return response

    def get_drawn_numbers(self, peer_id):
        """Показать все вытянутые числа"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
        
        drawn = self.games[peer_id]["drawn_numbers"]
        if not drawn:
            return "🎲 Числа еще не вытягивались."
        
        response = f"🎯 Вытянутые числа ({len(drawn)}):\n"
        # Группируем числа по строкам для удобства
        response += " ".join(str(num) for num in drawn)
        
        return response

    def get_standings(self, peer_id):
        """Показать текущие результаты всех игроков"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
        
        results = self._get_game_results(peer_id)
        if not results:
            return "❌ Нет данных об игроках."
        
        # Сортируем игроков по количеству зачеркнутых чисел
        sorted_players = sorted(results.items(), key=lambda x: x[1]['marked_count'], reverse=True)
        
        response = "📊 ТЕКУЩИЕ РЕЗУЛЬТАТЫ:\n\n"
        
        for i, (player_id, data) in enumerate(sorted_players, 1):
            player_name = get_user_name(player_id)
            
            # Проверяем, исключен ли игрок
            if player_id in self.games[peer_id]["excluded_players"]:
                response += f"{i}. 🚨 {player_name}: ИСКЛЮЧЁН ЗА ЧИТЕРСТВО\n"
                continue
            
            # Проверяем, есть ли у игрока заполненные линии
            card = self.games[peer_id]["players"][player_id]
            drawn_numbers = set(self.games[peer_id]["drawn_numbers"])
            completed_lines = 0
            
            for row in card:
                row_numbers = set(num for num in row if num != 0)
                if row_numbers and row_numbers.issubset(drawn_numbers):
                    completed_lines += 1
            
            if completed_lines > 0:
                response += f"{i}. 🎉 {player_name}: {data['marked_count']}/{data['total_count']} чисел ({completed_lines} линий ✅)\n"
            else:
                response += f"{i}. {player_name}: {data['marked_count']}/{data['total_count']} чисел\n"
        
        return response

    def get_excluded_players(self, peer_id):
        """Показать список исключенных за читерство игроков"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
        
        excluded = self.games[peer_id]["excluded_players"]
        if not excluded:
            return "✅ Пока никто не исключен за читерство."
        
        response = "🚨 ИСКЛЮЧЕННЫЕ ЗА ЧИТЕРСТВО:\n\n"
        for player_id in excluded:
            player_name = get_user_name(player_id)
            response += f"❌ {player_name}\n"
        
        return response

    def end_game(self, peer_id, user_id):
        """Завершение игры (только ведущий)"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
            
        if self.games[peer_id]["host_id"] != user_id:
            host_name = get_user_name(self.games[peer_id]["host_id"])
            return f"❌ Только ведущий ({host_name}) может завершить игру!"
        
        del self.games[peer_id]
        return "🎮 Игра в лото завершена ведущим."

    def force_end_game(self, peer_id):
        """Принудительное завершение игры (для модераторов)"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
        
        del self.games[peer_id]
        return "🎮 Игра в лото принудительно завершена модератором."

    def cheat_attempt(self, peer_id, user_id):
        """Попытка подделать случайное число с карточки с риском быть пойманным"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
            
        if not self.games[peer_id]["current_game"]:
            return "❌ Игра в лото уже завершена."
            
        if user_id not in self.games[peer_id]["players"]:
            return "❌ Вы не участвуете в этой игре."
            
        if user_id in self.games[peer_id]["excluded_players"]:
            return "❌ Вы исключены из игры за читерство!"

        # Получаем карточку игрока
        card = self.games[peer_id]["players"][user_id]
        drawn_numbers = set(self.games[peer_id]["drawn_numbers"])
        
        # Собираем все числа с карточки, которые еще не были вытянуты
        available_numbers = []
        for row in card:
            for num in row:
                if num != 0 and num not in drawn_numbers:
                    available_numbers.append(num)
        
        if not available_numbers:
            return "❌ У вас нет невытянутых чисел для подделки!"
        
        # Выбираем случайное число для подделки
        number = random.choice(available_numbers)
        
        # Генерируем шанс поймать читера (30%)
        caught = random.random() < 0.3
        
        player_name = get_user_name(user_id)
        
        if caught:
            # Игрока поймали!
            self.games[peer_id]["excluded_players"].append(user_id)
            
            response = f"🚨 ЧИТЕР ОБНАРУЖЕН! 🚨\n\n"
            response += f"🔍 {player_name} попытался подделать число {number}, но был пойман!\n"
            response += f"⚖️ {player_name} исключён из игры!\n\n"
            
            # Проверяем, остались ли активные игроки
            active_players = [pid for pid in self.games[peer_id]["players"].keys() 
                            if pid not in self.games[peer_id]["excluded_players"]]
            
            if len(active_players) <= 1:
                if active_players:
                    winner_name = get_user_name(active_players[0])
                    response += f"🏆 {winner_name} побеждает по умолчанию!\n"
                else:
                    response += "🎮 Все игроки исключены! Игра завершена.\n"
                self.games[peer_id]["current_game"] = False
                response += "🎮 Игра завершена!"
                
            return response
        else:
            # Игрок не пойман - добавляем число в вытянутые
            self.games[peer_id]["drawn_numbers"].append(number)
            
            response = f"😈 {player_name} тайно отметил число {number}...\n\n"
            response += f"🤫 Никто не заметил подлога!\n"
            response += f"📊 Число {number} добавлено к вытянутым числам.\n\n"
            
            # Проверяем на победителей после читерства
            winners = self._check_for_line_winners(peer_id)
            if winners and user_id in winners:
                response += f"🎉 {player_name} заполнил линию и побеждает!\n"
                response += f"😏 Но никто не знает, что это было читерством...\n\n"
                
                # Получаем результаты всех игроков
                results = self._get_game_results(peer_id)
                places = self._determine_places(results, winners)
                
                if places.get(2):
                    response += f"🥈 2-е место: {', '.join([get_user_name(pid) for pid in places[2]])} ({results[places[2][0]]['marked_count']} чисел)\n"
                
                if places.get(3):
                    response += f"🥉 3-е место: {', '.join([get_user_name(pid) for pid in places[3]])} ({results[places[3][0]]['marked_count']} чисел)\n"
                
                self.games[peer_id]["current_game"] = False
                response += "\n🎮 Игра завершена!"
            
            return response

    def _generate_bingo_card(self):
        """Генерация карточки лото 3x9 с числами от 1 до 90"""
        card = [[0 for _ in range(9)] for _ in range(3)]
        
        # Для каждого столбца определяем диапазон чисел
        for col in range(9):
            if col == 0:
                numbers = list(range(1, 10))
            elif col == 8:
                numbers = list(range(81, 91))
            else:
                numbers = list(range(col * 10, (col + 1) * 10))
            
            # Выбираем случайные числа для этого столбца
            selected = random.sample(numbers, 3)
            selected.sort()
            
            for row in range(3):
                card[row][col] = selected[row]
        
        # Заменяем некоторые числа на пустые места (0)
        for row in range(3):
            # В каждой строке должно быть 5 чисел и 4 пустых места
            positions_to_clear = random.sample(range(9), 4)
            for pos in positions_to_clear:
                card[row][pos] = 0
        
        return card

    def _format_card(self, card):
        """Форматирование карточки: только числа, по 5 в ряду, без разделителей"""
        result = ""
        for row in card:
            nums = [str(num).center(3) if num != 0 else "   " for num in row]
            # Оставляем только 5 чисел, остальные пустые
            filtered = [n for n in nums if n.strip()]
            while len(filtered) < 5:
                filtered.append("   ")
            result += " ".join(filtered) + "\n"
        return result

    def _format_card_with_marks(self, card, drawn_numbers):
        """Форматирование карточки с отметками: только числа, по 5 в ряду, без разделителей"""
        result = ""
        for row in card:
            nums = []
            for num in row:
                if num == 0:
                    continue
                elif num in drawn_numbers:
                    mark = f"✓{num}" if num >= 10 else f"✓{num}"
                    nums.append(mark.center(3))
                else:
                    nums.append(str(num).center(3))
            while len(nums) < 5:
                nums.append("   ")
            result += " ".join(nums) + "\n"
        return result

    def _check_for_line_winners(self, peer_id):
        """Проверка на победителей (заполненная горизонтальная линия)"""
        winners = []
        drawn_numbers = set(self.games[peer_id]["drawn_numbers"])
        excluded_players = set(self.games[peer_id]["excluded_players"])
        
        for player_id, card in self.games[peer_id]["players"].items():
            # Исключенные игроки не могут победить
            if player_id in excluded_players:
                continue
                
            # Проверяем каждую горизонтальную линию
            for row in card:
                # Собираем все числа в строке (кроме пустых мест)
                row_numbers = set(num for num in row if num != 0)
                
                # Если все числа в строке зачеркнуты - у игрока бинго
                if row_numbers and row_numbers.issubset(drawn_numbers):
                    winners.append(player_id)
                    break  # Достаточно одной заполненной линии
        
        return winners

    def _get_game_results(self, peer_id):
        """Получить результаты всех игроков (количество зачеркнутых чисел)"""
        results = {}
        drawn_numbers = set(self.games[peer_id]["drawn_numbers"])
        
        for player_id, card in self.games[peer_id]["players"].items():
            # Подсчитываем зачеркнутые числа
            marked_count = 0
            total_count = 0
            
            for row in card:
                for num in row:
                    if num != 0:
                        total_count += 1
                        if num in drawn_numbers:
                            marked_count += 1
            
            results[player_id] = {
                'marked_count': marked_count,
                'total_count': total_count
            }
        
        return results

    def _determine_places(self, results, winners):
        """Определить 2-е и 3-е места по количеству зачеркнутых чисел"""
        # Исключаем победителей из подсчета мест
        remaining_players = {pid: data for pid, data in results.items() if pid not in winners}
        
        if not remaining_players:
            return {}
        
        # Сортируем по количеству зачеркнутых чисел (по убыванию)
        sorted_players = sorted(remaining_players.items(), key=lambda x: x[1]['marked_count'], reverse=True)
        
        places = {}
        current_place = 2  # Начинаем с 2-го места (1-е уже занято победителями)
        i = 0
        
        while i < len(sorted_players) and current_place <= 3:
            current_score = sorted_players[i][1]['marked_count']
            same_score_players = []
            
            # Собираем всех игроков с одинаковым результатом
            while i < len(sorted_players) and sorted_players[i][1]['marked_count'] == current_score:
                same_score_players.append(sorted_players[i][0])
                i += 1
            
            if same_score_players:
                places[current_place] = same_score_players
                current_place += len(same_score_players)  # Следующее место сдвигается
        
        return places

    def _analyze_lines(self, card, drawn_numbers):
        """Анализ состояния горизонтальных линий"""
        analysis = ""
        drawn_set = set(drawn_numbers)
        
        for i, row in enumerate(card, 1):
            row_numbers = [num for num in row if num != 0]
            if not row_numbers:
                continue
                
            marked_in_row = [num for num in row_numbers if num in drawn_set]
            remaining_in_row = [num for num in row_numbers if num not in drawn_set]
            
            if len(remaining_in_row) == 0:
                analysis += f"🎉 Линия {i}: ЗАПОЛНЕНА!\n"
            elif len(remaining_in_row) == 1:
                analysis += f"🔥 Линия {i}: осталось 1 число ({remaining_in_row[0]})\n"
            elif len(remaining_in_row) == 2:
                analysis += f"⚡ Линия {i}: осталось 2 числа ({', '.join(map(str, remaining_in_row))})\n"
            else:
                analysis += f"📋 Линия {i}: отмечено {len(marked_in_row)}/{len(row_numbers)}\n"
        
        return analysis.strip()