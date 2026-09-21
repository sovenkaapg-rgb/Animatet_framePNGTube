from config_manager import config

class AvatarController:
    def __init__(self, avatar_render, timeline_panel, mixer_panel):
        self.avatar = avatar_render
        self.timeline = timeline_panel
        self.mixer = mixer_panel
        
        # Системные переменные плавности
        self.silence_counter = 0
        self.current_talk_duration = 0
        self.current_shout_duration = 0
        self.talk_hold_timer = 0
        self.shout_hold_timer = 0
        self.post_shout_hold_timer = 0

    def update_frame_logic(self, vol, thresh_talk, thresh_shout, is_stream_mode):
        """Интеллектуальный расчет, какой кадр показать в зависимости от звука"""
        # 1. Режим РЕДАКТОРА
        if not is_stream_mode:
            if self.avatar.audio_state != "editor":
                self.avatar.audio_state = "editor"
                self.avatar.update()
            return
        
        # 2. Режим СТРИМА
        target_state = "idle"
        ticks_to_sleep_dynamic = config.afk_time_to_sleep * 33
        
        # БАГ ИСПРАВЛЕН: Переводим сырые значения слайдеров инерции в реальные тики (1 тик ≈ 30мс).
        # Теперь аватар мгновенно закрывает рот, а задержка соответствует выбранным секундам.
        MIN_SHOUT_TICKS = max(2, int(config.shout_inertia / 3))  
        MIN_TALK_TICKS = max(2, int(config.talk_inertia / 15))    
        
        if vol > thresh_shout:
            target_state = "shout"
            self.current_shout_duration += 1
            self.current_talk_duration = 0
            self.silence_counter = 0
            
            if self.current_shout_duration > 10:
                self.shout_hold_timer = MIN_SHOUT_TICKS + 4
            else:
                self.shout_hold_timer = MIN_SHOUT_TICKS
                
            self.post_shout_hold_timer = 4 
            
        elif vol > thresh_talk:
            if self.shout_hold_timer > 0:
                target_state = "shout"
                self.shout_hold_timer -= 1
            else:
                target_state = "talk"
                self.current_talk_duration += 1
                self.current_shout_duration = 0
                self.silence_counter = 0
                self.post_shout_hold_timer = 0
                
                if self.current_talk_duration > 12:
                    self.talk_hold_timer = MIN_TALK_TICKS * 2
                else:
                    self.talk_hold_timer = MIN_TALK_TICKS
        else:
            # Зона тишины — отрабатываем таймеры удержания по приоритету
            self.current_talk_duration = 0
            self.current_shout_duration = 0
            
            if self.shout_hold_timer > 0:
                target_state = "shout"
                self.shout_hold_timer -= 1
            elif self.post_shout_hold_timer > 0:
                target_state = "talk" 
                self.post_shout_hold_timer -= 1
            elif self.talk_hold_timer > 0:
                target_state = "talk"
                self.talk_hold_timer -= 1
            else:
                if self.avatar.audio_state == "sleep":
                    target_state = "sleep"
                    self.silence_counter = ticks_to_sleep_dynamic
                else:
                    self.silence_counter += 1
                    if self.silence_counter >= ticks_to_sleep_dynamic:
                        target_state = "sleep"
                    else:
                        target_state = "idle"
        
        # Обновляем состояние аватара только при реальной смене фазы
        if self.avatar.audio_state != target_state:
            if target_state in ["talk", "shout", "idle"]:
                self.silence_counter = 0
            self.avatar.audio_state = target_state
            self.avatar.update()

    def reset_timers(self):
        """Сброс счетчиков при выходе из стрима"""
        self.silence_counter = 0
        self.talk_hold_timer = 0
        self.shout_hold_timer = 0
        self.post_shout_hold_timer = 0
