import requests
import time
import threading
from PyQt6.QtCore import QObject, pyqtSignal


class TwitchManager(QObject):
    rewards_loaded = pyqtSignal(list)      # (список словарей с наградами)
    reward_redeemed = pyqtSignal(str, str) # (username, reward_title)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.token = ""
        self.client_id = ""
        self.broadcaster_id = ""
        self.is_running = False

    def connect(self, token, client_id, channel_name):
        """Подключение и получение ID канала"""
        self.token = token
        self.client_id = client_id
        
        headers = {
            'Client-ID': client_id, 
            'Authorization': f'Bearer {token}'
        }
        
        try:
            # 1. Получаем ID стримера по нику
            r = requests.get(f'https://api.twitch.tv/helix/users?login={channel_name}', headers=headers)
            if r.status_code == 200:
                data = r.json()
                if data['data']:
                    self.broadcaster_id = data['data'][0]['id']
                    self.load_rewards()
                    self.is_running = True
                    # Запускаем фоновый поток опроса наград
                    threading.Thread(target=self.poll_loop, daemon=True).start()
                else:
                    self.error.emit(f"Канал '{channel_name}' не найден")
            else:
                self.error.emit(f"Ошибка API: {r.status_code}. Проверь токен и Client ID")
        except Exception as e:
            self.error.emit(f"Ошибка подключения: {e}")

    def load_rewards(self):
        """Загружает список активных наград канала"""
        headers = {'Client-ID': self.client_id, 'Authorization': f'Bearer {self.token}'}
        r = requests.get(f'https://api.twitch.tv/helix/channel_points/custom_rewards?broadcaster_id={self.broadcaster_id}', headers=headers)
        
        if r.status_code == 200:
            rewards = []
            for item in r.json().get('data', []):
                if item['is_enabled'] and not item['is_paused']:
                    rewards.append({
                        'id': item['id'], 
                        'title': item['title'], 
                        'cost': item['cost']
                    })
            self.rewards_loaded.emit(rewards)
        else:
            self.error.emit(f"Не удалось загрузить награды: {r.status_code}")

    def poll_loop(self):
        """Фоновый цикл: проверяет новые выкупы каждые 5 секунд"""
        last_ids = set()
        headers = {'Client-ID': self.client_id, 'Authorization': f'Bearer {self.token}'}
        
        while self.is_running:
            try:
                # Запрашиваем только выполненные (FULFILLED) награды
                r = requests.get(f'https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions?broadcaster_id={self.broadcaster_id}&status=FULFILLED', headers=headers)
                if r.status_code == 200:
                    for item in r.json().get('data', []):
                        if item['id'] not in last_ids:
                            last_ids.add(item['id'])
                            # Ограничим память, чтобы не росла бесконечно
                            if len(last_ids) > 100:
                                last_ids = set(list(last_ids)[-50:])
                            
                            user = item.get('user_name', 'Anon')
                            title = item['reward']['title']
                            self.reward_redeemed.emit(user, title)
            except Exception:
                pass
            time.sleep(5)