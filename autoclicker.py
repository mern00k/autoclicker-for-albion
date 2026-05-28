import customtkinter as ctk
from pystray import MenuItem as item
import pystray
from PIL import Image, ImageDraw, ImageFilter 
import threading
import time
import keyboard
import pydirectinput
import sys
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class UltimateClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Albion Clicker v4.3.1")
        
        self.root.geometry("410x460")
        self.root.resizable(False, False)
        
        self.active = False 
        self.icon = None
        self.binds_list = [
        {"trigger": "q", "spam": "q", "active": False}
        ]
        self.key_toggle = 'ctrl+p'  # Чем включаем/выключаем (HotKey)
        """Бинд для включения выключения ПРОСЛУШИВАНИЯ"""
        
        self.is_waiting_spam_key_window = False # Флаг для смены клавиш спама
        self.is_waiting_toggle_key = False # Флаг для смены клавиши управления
        
        # Главный контейнер с отступами, чтобы элементы не прижимались к краям
        main_container = ctk.CTkFrame(root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=15)
        self.is_visible = True
        
        # Красивая закругленная плашка для СТАТУСА
        self.status_frame = ctk.CTkFrame(main_container, fg_color="#E74C3C", corner_radius=10, height=45)
        self.status_frame.pack(fill="x", pady=(0, 15))
        self.status_frame.pack_propagate(False) # Фиксируем высоту плашки

        self.status_label = ctk.CTkLabel(self.status_frame, text="СТАТУС: ВЫКЛЮЧЕНО", font=("Arial", 14, "bold"), text_color="white")
        self.status_label.pack(expand=True)

        # Интерактивная Главная Кнопка
        self.btn = ctk.CTkButton(main_container, text=f"ВКЛ ПРОСМОТР KEY: {self.key_toggle.upper()}", font=("Arial", 13, "bold"), height=40, corner_radius=8, fg_color="#3498DB", hover_color="#2980B9", command=self.toggle_monitor)
        self.btn.pack(fill="x", pady=(0, 15))

        # Кнопка для скрывания списка биндов
        self.btn_toggle = ctk.CTkButton(main_container, text="Свернуть окно", command=self.toggle_scroll)
        self.btn_toggle.pack(pady=10)
        
        # Кнопка адд бинд
        self.btn_add_bind = ctk.CTkButton(
        main_container, 
        text="➕ ДОБАВИТЬ НОВЫЙ БИНД", 
        fg_color="#2ECC71", 
        hover_color="#27AE60", 
        font=("Arial", 12, "bold"),
        command=self.open_add_bind_window
)
        self.btn_add_bind.pack(pady=5, fill="x")
        
        # Пролистываемые бинды
        self.scrollable_frame = ctk.CTkScrollableFrame(main_container, width=350, height=200)
        self.scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)
        self.refresh_binds_ui()

        # Отдельная нижняя панель под горячие клавиши управления окном
        self.help_panel = ctk.CTkFrame(main_container, fg_color="#212F3D", corner_radius=8)
        self.help_panel.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.help_panel, text="Клавиши управления (Управление окном):", font=("Arial", 11, "bold"), text_color="#95A5A6", anchor="w").pack(fill="x", padx=15, pady=(8, 4))
        
        controls = [
            ("Клавиша [ 9 ]", "Свернуть в системный трей"),
            ("Клавиша [ 0 ]", "Добавить кнопку спама"),
            ("Клавиша [ 8 ]", "Изменить кнопку активации"),
            ("Клавиша [Esc]", "Полное закрытие кликера")
        ]
        
        for key_text, desc_text in controls:
            row = ctk.CTkFrame(self.help_panel, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(row, text=key_text, font=("Arial", 11, "bold"), text_color="#3498DB", width=95, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"—  {desc_text}", font=("Arial", 11), text_color="#BDC3C7", anchor="w").pack(side="left", fill="x")

        # =====================================================================

        threading.Thread(target=self.main_loop, daemon=True).start()
        threading.Thread(target=self.hotkey_listener, daemon=True).start()
        
        self.root.bind('<Escape>', lambda e: self.on_exit())
        self.root.bind('9', lambda e: self.withdraw_to_tray())
        self.root.bind('0', lambda e: self.open_add_bind_window())
        self.root.bind('8', lambda e: self.start_binding())

    def start_binding(self):
        """Включает режим ожидания новой комбинации клавиш"""
        self.active = False 
        self.btn.configure(text=f"ВКЛ ПРОСМОТР KEY: {self.key_toggle.upper()}")
        self.update_ui("НАЖМИТЕ ХОТКЕЙ...", "#86005C")

        # Запускаем чтение хоткея в отдельном потоке, чтобы не вешать GUI
        threading.Thread(target=self._capture_hotkey, daemon=True).start()

    def _capture_hotkey(self):
        """Записывает комбинации клавиш через(keyboard) для toggle_key"""
        # Метод заблокирует этот поток, пока вы не нажмете и не отпустите сочетание клавиш
        time.sleep(0.3)
        new_hotkey = keyboard.read_hotkey(suppress=False)
        
        not_keys = ['8', '9', '0', 'Escape']
        for bind in self.binds_list:
            not_keys.append(bind["trigger"].lower())
            not_keys.append(bind["spam"].lower())
        
        if new_hotkey.lower() not in not_keys:
            # Записываем полученную строку комбинации (например, 'ctrl+shift+x')
            self.key_toggle = new_hotkey
            # Возвращаем интерфейс в исходное состояние через after для безопасности потоков
            self.root.after(0, lambda: self.update_ui("СТАТУС: ВЫКЛЮЧЕНО", "#E74C3C"))

    def close_popup_safely(self):
        """Безопасно закрывает окно и возвращает статус кликера"""
        self.is_waiting_spam_key_window = False
        # Возвращаем статус кликер который был до открытия окна
        self.active = self.was_active_before_popup
        if self.active:
            self.update_ui("СТАТУС: ОЖИДАНИЕ", "#F88400")
        else:
            self.update_ui("СТАТУС: ВЫКЛЮЧЕНО", "#E74C3C")

        self.popup.destroy()
    
    def open_add_bind_window(self):
        """Открывает окно добавления бинда"""
        # временно отключаем кликер, чтобы он не спамил во время настройки бинда
        self.was_active_before_popup = self.active
        self.active = False
        self.temp_trigger = None
        self.temp_spam = None
        self.is_waiting_spam_key_window = True # Флаг открытого окна
        
        self.update_ui("НАСТРОЙКА БИНДА...", "#86005C")
        self.popup = ctk.CTkToplevel(self.root)
        self.popup.title("Новый бинд")
        self.popup.geometry("340x200")
        self.popup.resizable(False, False)

        # Делаем окно модальным (фокус только на нем)
        self.popup.grab_set()
        self.popup.focus_set()

        # Перехватываем закрытие окна "на крестик", чтобы корректно вернуть настройки
        self.popup.protocol("WM_DELETE_WINDOW", self.close_popup_safely)
        
        # Текстовая подсказка для пользователя
        self.popup_label = ctk.CTkLabel(
            self.popup, 
            text="Нажмите клавишу,\nкоторую будете ЗАЖИМАТЬ", 
            font=("Arial", 13, "bold"),
            pady=20
        )
        self.popup_label.pack(expand=True, fill="both")

        # Переменные для временного хранения клавиш перед записью
        self.temp_trigger = None
        self.temp_spam = None

        # Привязываем перехват абсолютно любой нажатой клавиши к этому окну
        self.popup.bind("<Key>", self.process_popup_key)
    
    def process_popup_key(self, event):
        """Пошагово записывает клавиши по их физическому коду (keycode)"""
        
        HARDWARE_KEYMAP = {
        65: "a", 66: "b", 67: "c", 68: "d", 69: "e", 70: "f", 71: "g", 72: "h",
        73: "i", 74: "j", 75: "k", 76: "l", 77: "m", 78: "n", 79: "o", 80: "p",
        81: "q", 82: "r", 83: "s", 84: "t", 85: "u", 86: "v", 87: "w", 88: "x",
        89: "y", 90: "z",
        48: "0", 49: "1", 50: "2", 51: "3", 52: "4", 53: "5", 54: "6", 55: "7", 56: "8", 57: "9",
        112: "f1", 113: "f2", 114: "f3", 115: "f4", 116: "f5", 117: "f6", 
        118: "f7", 119: "f8", 120: "f9", 121: "f10", 122: "f11", 123: "f12",
        32: "space", 13: "enter", 20: "caps lock", 9: "tab", 16: "shift", 17: "ctrl", 18: "alt"
    }
        sys_keycode = event.keycode
        key_name = HARDWARE_KEYMAP.get(sys_keycode, event.keysym.lower())
        
        if key_name is None:
            return

        if key_name == "return": key_name = "enter"
        if key_name == "caps_lock": key_name = "caps lock"
        
        # Игнорируем системные модификаторы, кнопки управления окном и ошибочные символы
        if key_name in ["shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r", "0", "8", "9", "escape", "??"]:
            return
        
        # ШАГ 1: Записываем клавишу-триггер (что зажимать)
        if self.temp_trigger is None:
            self.temp_trigger = key_name
            self.temp_trigger_readable = key_name.upper() # запоминаем красивое имя для UI

            self.popup_label.configure(
                text=f"Триггер: [{key_name.upper()}]\n\nТеперь нажмите клавишу,\nкоторую нужно СПАМИТЬ"
            )
            return

        # Записываем клавишу для спама (что отправлять в игру)
        if self.temp_spam is None:
            self.temp_spam = key_name

            # Сохраняем готовый бинд в наш список (записываем и скан-код, и имя для отображения)
            self.binds_list.append({
                "trigger": self.temp_trigger,
                "trigger_name": self.temp_trigger_readable,
                "spam": self.temp_spam,
                "spam_name": key_name.upper(),
                "active": False
            })

            # Закрываем всплывающее окно через наш безопасный метод и обновляем список
            self.close_popup_safely()
            self.refresh_binds_ui()
            
    def hotkey_listener(self):
        while True:
            if keyboard.is_pressed(self.key_toggle):
                self.toggle_monitor()
                time.sleep(0.3)
            time.sleep(0.01)

    # --- Трей ---
    def create_tray_icon(self):
        size = 256

        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # Черный фон
        d.rounded_rectangle(
            (8, 8, 248, 248),
            radius=45,
            fill=(10, 10, 10),
            outline=(0, 220, 255),
            width=10
        )

        # Внешнее свечение
        glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)

        gd.rounded_rectangle(
            (8, 8, 248, 248),
            radius=45,
            outline=(0, 220, 255, 120),
            width=18
        )

        glow = glow.filter(ImageFilter.GaussianBlur(12))

        img = Image.alpha_composite(glow, img)

        d = ImageDraw.Draw(img)

        # Буква Q
        q_color = (0, 220, 255)

        # Основной круг
        d.ellipse(
            (70, 60, 185, 175),
            outline=q_color,
            width=20
        )

        # Хвостик Q
        d.line(
            (145, 145, 195, 195),
            fill=q_color,
            width=20
        )

        # Сглаживание хвостика
        d.ellipse(
            (135, 135, 155, 155),
            fill=q_color
        )

        d.ellipse(
            (185, 185, 205, 205),
            fill=q_color
        )

        menu = (
        item('Прослушивание Off-On', self.toggle_monitor),
        item('Развернуть', self.show_from_tray),
        item('Выход', self.on_exit)
        )

        self.icon = pystray.Icon(
            "clicker",
            img.resize((64, 64), Image.Resampling.LANCZOS),
            "Clicker v4.3.1",
            menu
        )

        self.icon.run()

    def withdraw_to_tray(self):
        if not self.icon or not self.icon.visible:
            self.root.withdraw()
            threading.Thread(target=self.create_tray_icon, daemon=True).start()

    def show_from_tray(self, icon=None, item=None):
        if self.icon: self.icon.stop()
        self.icon = None
        self.root.after(0, self.root.deiconify)

    def on_exit(self, icon=None, item=None):
        if self.icon: self.icon.stop()
        self.root.destroy()
        sys.exit()
            
    # --- Логика кликера ---
    def toggle_monitor(self):
        self.active = not self.active
        if self.active:
            self.root.after(0, lambda: self.btn.configure(text=f"ВЫКЛ ПРОСМОТР KEY: {self.key_toggle.upper()}"))
            self.update_ui(f"СТАТУС: ОЖИДАНИЕ", "#F88400") 
        else:
            self.root.after(0, lambda: self.btn.configure(text=f"ВКЛ ПРОСМОТР KEY: {self.key_toggle.upper()}"))
            self.update_ui("СТАТУС: ВЫКЛЮЧЕНО", "#E74C3C") 

    def update_ui(self, text, color):
        self.root.after(0, lambda: self.status_frame.configure(fg_color=color))
        self.root.after(0, lambda: self.status_label.configure(text=text))
        
    def delete_bind(self, index):
        self.binds_list.pop(index) # Удаляем из структуры данных
        self.refresh_binds_ui()     # Перерисовываем интерфейс
        
    def refresh_binds_ui(self):
    # 1. Сначала полностью очищаем старые виджеты из фрейма прокрутки
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # 2. Строим новые плашки для каждого бинда из нашего списка
        for index, bind in enumerate(self.binds_list):
            # Строка-контейнер для одного бинда
            row = ctk.CTkFrame(self.scrollable_frame, fg_color="#2C3E50", corner_radius=6)
            row.pack(fill="x", pady=4, padx=5)

            # Текст бинда
            text = f"Если зажата [{bind.get('trigger_name', bind['trigger']).upper()}] ➔ Спамим [{bind.get('spam_name', bind['spam']).upper()}]"
            label = ctk.CTkLabel(row, text=text, font=("Arial", 10, "bold"))
            label.pack(side="left", padx=10, pady=5)

            # Кнопка удаления конкретного бинда (по индексу)
            btn_delete = ctk.CTkButton(
                row, 
                text="❌", 
                width=30, 
                fg_color="#E74C3C", 
                hover_color="#C0392B",
                command=lambda i=index: self.delete_bind(i)
            )
            btn_delete.pack(side="right", padx=5, pady=5)    
    
    def toggle_scroll(self):
        if self.is_visible:
            # Скрываем внутреннее окно
            self.scrollable_frame.pack_forget()
            self.btn_toggle.configure(text="Развернуть окно")
            self.is_visible = False
        else:
            # Возвращаем внутреннее окно на место
            self.scrollable_frame.pack(pady=10, padx=20, fill="x", before=self.help_panel)
            self.btn_toggle.configure(text="Свернуть окно")
            self.refresh_binds_ui()
            self.is_visible = True

    def main_loop(self):
        while True:
            if not self.active:
                time.sleep(0.01)
                continue

            for bind in self.binds_list:
                trigger_key = bind["trigger"] 
                spam_key = bind["spam"]     

                try:
                    # 1. Проверяем, зажал ли пользователь триггер
                    if keyboard.is_pressed(trigger_key):
                        self.update_ui("СТАТУС: ЗАЛИВАЕМ!", "#2ECC71")

                        while keyboard.is_pressed(trigger_key) and self.active:
                            pydirectinput.press(spam_key)
                            time.sleep(0.06) 

                        self.update_ui("СТАТУС: ОЖИДАНИЕ", "#F88400")
                except Exception:
                    continue

            time.sleep(0.01)
            
if __name__ == "__main__":
    pydirectinput.PAUSE = 0
    root = ctk.CTk()
    app = UltimateClicker(root)
    root.mainloop()
