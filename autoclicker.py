import customtkinter as ctk
from pystray import MenuItem as item
import pystray
from PIL import Image, ImageDraw
import threading
import time
import keyboard
import sys
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class UltimateClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Albion Clicker v5")
        
        # --- ИЗМЕНЕНА СТРОКА: Увеличили размер окна для стильного размещения элементов ---
        self.root.geometry("380x420")
        self.root.resizable(False, False)
        
        self.active = False 
        self.icon = None
        self.key_spam = 'q'     # Что спамим
        self.key_toggle = 'f1'  # Чем включаем/выключаем (HotKey)
        
        self.is_waiting_spam_key = False  # Флаг для смены клавиши спама
        self.is_waiting_toggle_key = False # Флаг для смены клавиши управления

        # =====================================================================
        # 🔥 ПОЛНОСТЬЮ ОБНОВЛЕННЫЙ БЛОК UI (Строки 26-42 оригинального кода)
        # =====================================================================
        
        # Главный контейнер с отступами, чтобы элементы не прижимались к краям
        main_container = ctk.CTkFrame(root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Красивая закругленная плашка для СТАТУСА
        self.status_frame = ctk.CTkFrame(main_container, fg_color="#E74C3C", corner_radius=10, height=45)
        self.status_frame.pack(fill="x", pady=(0, 15))
        self.status_frame.pack_propagate(False) # Фиксируем высоту плашки

        self.status_label = ctk.CTkLabel(self.status_frame, text="СТАТУС: ВЫКЛЮЧЕНО", font=("Arial", 14, "bold"), text_color="white")
        self.status_label.pack(expand=True)

        # 2. Интерактивная Главная Кнопка
        self.btn = ctk.CTkButton(main_container, text="ВКЛЮЧИТЬ ПРОСМОТР", font=("Arial", 13, "bold"), height=40, corner_radius=8, fg_color="#3498DB", hover_color="#2980B9", command=self.toggle_monitor)
        self.btn.pack(fill="x", pady=(0, 15))

        # 3. Стильный блок «Какая кнопка нажата ➡️ Какая спамится»
        binds_container = ctk.CTkFrame(main_container, fg_color="#2C3E50", corner_radius=10, border_width=1, border_color="#34495E")
        binds_container.pack(fill="x", pady=(0, 15), padx=5)
        
        # Левая колонка: Условие зажатия
        left_box = ctk.CTkFrame(binds_container, fg_color="transparent")
        left_box.pack(side="left", expand=True, fill="both", pady=10)
        ctk.CTkLabel(left_box, text="ЕСЛИ ЗАЖАТЬ", font=("Arial", 10, "bold"), text_color="#BDC3C7").pack()
        self.info_spam = ctk.CTkLabel(left_box, text=self.key_spam.upper(), font=("Arial", 22, "bold"), text_color="#2ECC71")
        self.info_spam.pack()

        # Разделитель-стрелочка по центру
        ctk.CTkLabel(binds_container, text="➔", font=("Arial", 20, "bold"), text_color="#7F8C8D").pack(side="left", pady=10)

        # Правая колонка: Что будет спамиться
        right_box = ctk.CTkFrame(binds_container, fg_color="transparent")
        right_box.pack(side="right", expand=True, fill="both", pady=10)
        ctk.CTkLabel(right_box, text="БУДЕТ СПАМИТЬ", font=("Arial", 10, "bold"), text_color="#BDC3C7").pack()
        self.info_toggle = ctk.CTkLabel(right_box, text=self.key_toggle.upper(), font=("Arial", 18, "bold"), text_color="#3498DB")
        self.info_toggle.pack()

        # 4. Отдельная нижняя панель под горячие клавиши управления окном
        help_panel = ctk.CTkFrame(main_container, fg_color="#212F3D", corner_radius=8)
        help_panel.pack(fill="both", expand=True)
        
        ctk.CTkLabel(help_panel, text="Клавиши управления (Управление окном):", font=("Arial", 11, "bold"), text_color="#95A5A6", anchor="w").pack(fill="x", padx=15, pady=(8, 4))
        
        # Удобная и читаемая таблица биндов
        controls = [
            ("Клавиша [ 9 ]", "Свернуть в системный трей"),
            ("Клавиша [ 0 ]", "Изменить кнопку спама"),
            ("Клавиша [ 8 ]", "Изменить кнопку активации"),
            ("Клавиша [Esc]", "Полное закрытие кликера")
        ]
        
        for key_text, desc_text in controls:
            row = ctk.CTkFrame(help_panel, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(row, text=key_text, font=("Arial", 11, "bold"), text_color="#3498DB", width=95, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"—  {desc_text}", font=("Arial", 11), text_color="#BDC3C7", anchor="w").pack(side="left", fill="x")

        # =====================================================================

        threading.Thread(target=self.main_loop, daemon=True).start()
        threading.Thread(target=self.hotkey_listener, daemon=True).start()
        
        self.root.bind('<Escape>', lambda e: self.on_exit())
        self.root.bind('9', lambda e: self.withdraw_to_tray())
        self.root.bind('0', lambda e: self.start_binding("spam"))
        self.root.bind('8', lambda e: self.start_binding("toggle"))
        self.root.bind('<Key>', self.apply_key_bind)

    def start_binding(self, mode):
        """Включает режим ожидания новой клавиши"""
        self.active = False 
        # --- ИЗМЕНЕНА СТРОКА: Заменено .config на .configure (Специфика CustomTkinter) ---
        self.btn.configure(text="ВКЛЮЧИТЬ ПРОСМОТР")
        
        if mode == "spam":
            self.is_waiting_spam_key = True
            self.is_waiting_toggle_key = False
            self.update_ui("ЖДУ КЛАВИШУ СПАМА...", "#86005C") # Используем красивый оранжевый HEX
        else:
            self.is_waiting_toggle_key = True
            self.is_waiting_spam_key = False
            self.update_ui("ПЕРЕПРИВЯЗКА...", "#86005C")

    def apply_key_bind(self, event):
        """Сохраняет нажатую клавишу"""
        if event.keysym in ['0', '8', '9', 'Escape']:
            return

        key = event.char if event.char and event.char != "" else event.keysym
        
        if self.is_waiting_spam_key:
            self.key_spam = key
            self.is_waiting_spam_key = False
        elif self.is_waiting_toggle_key:
            self.key_toggle = key
            self.is_waiting_toggle_key = False

        # --- ИЗМЕНЕНЫ СТРОКИ: Обновление текста в новых карточках биндов ---
        self.info_spam.configure(text=self.key_spam.upper())
        self.info_toggle.configure(text=self.key_toggle.upper())
        self.update_ui("СТАТУС: ВЫКЛЮЧЕНО", "#E74C3C")

    def hotkey_listener(self):
        while True:
            if keyboard.is_pressed(self.key_toggle) and not (self.is_waiting_spam_key or self.is_waiting_toggle_key):
                self.toggle_monitor()
                time.sleep(0.3)
            time.sleep(0.01)

    # --- Трей ---
    def create_tray_icon(self):
        img = Image.new('RGB', (64, 64), "red")
        d = ImageDraw.Draw(img)
        d.ellipse((16, 16, 48, 48), fill="white")
        menu = (item('Развернуть', self.show_from_tray), item('Выход', self.on_exit))
        self.icon = pystray.Icon("clicker", img, "Clicker v5", menu)
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
            self.root.after(0, lambda: self.btn.configure(text="ВЫКЛЮЧИТЬ ПРОСМОТР"))
            self.update_ui(f"СТАТУС: ОЖИДАНИЕ ({self.key_spam.upper()})", "#F88400") # Приятный синий HEX
        else:
            self.root.after(0, lambda: self.btn.configure(text="ВКЛЮЧИТЬ ПРОСМОТР"))
            self.update_ui("СТАТУС: ВЫКЛЮЧЕНО", "#E74C3C") # Красивый красный HEX

    # --- ИЗМЕНЕНА ФУНКЦИЯ: Теперь меняется не цвет букв, а цвет фоновой плашки статуса для максимального стиля ---
    def update_ui(self, text, color):
        self.root.after(0, lambda: self.status_frame.configure(fg_color=color))
        self.root.after(0, lambda: self.status_label.configure(text=text))

    def main_loop(self):
        while True:
            if self.active and not (self.is_waiting_spam_key or self.is_waiting_toggle_key):
                if keyboard.is_pressed(self.key_spam):
                    self.update_ui("СТАТУС: ЗАЛИВАЕМ!", "#2ECC71") # Яркий зеленый HEX
                    while keyboard.is_pressed(self.key_spam) and self.active:
                        keyboard.write(self.key_spam) 
                        time.sleep(0.05)
                    self.update_ui(f"СТАТУС: ОЖИДАНИЕ ({self.key_spam.upper()})", "#F88400")
            time.sleep(0.01)

if __name__ == "__main__":
    root = ctk.CTk()
    app = UltimateClicker(root)
    root.mainloop()
