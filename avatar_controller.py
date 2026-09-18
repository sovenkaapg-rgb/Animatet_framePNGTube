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

        if vol > thresh_shout:
            # СЕЙЧАС КРИЧИТ
            target_state = "shout"
            self.current_shout_duration += 1
            self.current_talk_duration = 0
            self.silence_counter = 0
            self.post_shout_hold_timer = 0
            
            if self.current_shout_duration > 13:
                self.shout_hold_timer = config.shout_inertia
            else:
                self.shout_hold_timer = max(2, config.shout_inertia // 4)

        elif vol > thresh_talk:
            # ГОВОРИТ
            target_state = "talk"
            self.current_talk_duration += 1
            self.current_shout_duration = 0
            self.silence_counter = 0
            self.post_shout_hold_timer = 0
            
            if self.current_talk_duration > 16:
                self.talk_hold_timer = config.talk_inertia * 2
            else:
                self.talk_hold_timer = config.talk_inertia

        else:
            # ТИШИНА
            self.current_talk_duration = 0
            self.current_shout_duration = 0
            
            if self.post_shout_hold_timer > 0:
                target_state = "shout"
                self.post_shout_hold_timer -= 1
                self.shout_hold_timer = 0
                self.talk_hold_timer = 0
                
            elif self.shout_hold_timer > 0:
                target_state = "shout"
                self.shout_hold_timer -= 1
                
            elif self.talk_hold_timer > 0:
                target_state = "talk"
                self.talk_hold_timer -= 1
                
            else:
                # Вся инерция вышла — считаем время до сна
                if self.avatar.audio_state == "sleep":
                    target_state = "sleep"
                    self.silence_counter = ticks_to_sleep_dynamic
                else:
                    self.silence_counter += 1
                    if self.silence_counter >= ticks_to_sleep_dynamic:
                        target_state = "sleep"
                    else:
                        target_state = "idle"

        # Применяем вычисленный кадр и сбрасываем счетчик при пробуждении
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
