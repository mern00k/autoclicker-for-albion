import tkinter as tk
from pystray import MenuItem as item
import pystray
from PIL import Image, ImageDraw
import threading
import time
import keyboard
import sys

class UltimateClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Кликер от мернока v5")
        self.root.geometry("300x260")
        
        self.active = False 
        self.icon = None
        self.key_spam = 'q'     # Что спамим
        self.key_toggle = 'f1'  # Чем включаем/выключаем (HotKey)
        
        self.is_waiting_spam_key = False  # Флаг для смены клавиши спама
        self.is_waiting_toggle_key = False # Флаг для смены клавиши управления

        # UI
        self.status_label = tk.Label(root, text="Статус: ты аутист", font=("Arial", 12), fg="red")
        self.status_label.pack(pady=10)
        
        self.btn = tk.Button(root, text="ВКЛЮЧИТЬ ПРОСМОТР", command=self.toggle_monitor)
        self.btn.pack(pady=5)
        
        self.info_spam = tk.Label(root, text=f"Спам: {self.key_spam.upper()}", font=("Arial", 9, "bold"))
        self.info_spam.pack()
        
        self.info_toggle = tk.Label(root, text=f"Вкл/Выкл: {self.key_toggle.upper()}", font=("Arial", 9, "bold"))
        self.info_toggle.pack()
        
        tk.Label(root, text="Бинды в окне:\n9: Трей | 0: Смена спама | 8: Смена key Просмотра\nEsc: Выход", fg="gray", justify="left").pack(pady=10)

        threading.Thread(target=self.main_loop, daemon=True).start()
        threading.Thread(target=self.hotkey_listener, daemon=True).start() # Слушаем HotKey отдельно
        
        # Бинды управления окном
        self.root.bind('<Escape>', lambda e: self.on_exit())
        self.root.bind('9', lambda e: self.withdraw_to_tray())
        self.root.bind('0', lambda e: self.start_binding("spam"))
        self.root.bind('8', lambda e: self.start_binding("toggle"))
        self.root.bind('<Key>', self.apply_key_bind)

    def start_binding(self, mode):
        """Включает режим ожидания новой клавиши"""
        self.active = False 
        self.btn.config(text="ВКЛЮЧИТЬ ПРОСМОТР")
        
        if mode == "spam":
            self.is_waiting_spam_key = True
            self.is_waiting_toggle_key = False
            self.update_ui("ЖДУ КЛАВИШУ СПАМА...", "orange")
        else:
            self.is_waiting_toggle_key = True
            self.is_waiting_spam_key = False
            self.update_ui("ПЕРЕПРИВЯЗКА...", "orange")

    def apply_key_bind(self, event):
        """Сохраняет нажатую клавишу"""
        # Исключаем системные цифры
        if event.keysym in ['0', '8', '9', 'Escape']:
            return

        key = event.char if event.char and event.char != "" else event.keysym
        
        if self.is_waiting_spam_key:
            self.key_spam = key
            self.is_waiting_spam_key = False
        elif self.is_waiting_toggle_key:
            self.key_toggle = key
            self.is_waiting_toggle_key = False

        self.info_spam.config(text=f"Спам: {self.key_spam.upper()}")
        self.info_toggle.config(text=f"Вкл/Выкл: {self.key_toggle.upper()}")
        self.update_ui("Статус: ты аутист", "red")

    def hotkey_listener(self):
        """Слушает нажатие HotKey всегда (глобально)"""
        while True:
            # Если нажата клавиша управления и мы не в режиме перебинда
            if keyboard.is_pressed(self.key_toggle) and not (self.is_waiting_spam_key or self.is_waiting_toggle_key):
                self.toggle_monitor()
                time.sleep(0.3) # Защита от дребезга (чтобы не переключалось 100 раз в секунду)
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
            self.root.after(0, lambda: self.btn.config(text="ВЫКЛЮЧИТЬ ПРОСМОТР"))
            self.update_ui(f"Статус: ОЖИДАНИЕ ({self.key_spam.upper()})", "blue")
        else:
            self.root.after(0, lambda: self.btn.config(text="ВКЛЮЧИТЬ ПРОСМОТР"))
            self.update_ui("Статус: ты аутист", "red")

    def update_ui(self, text, color):
        self.root.after(0, lambda: self.status_label.config(text=text, fg=color))

    def main_loop(self):
        while True:
            if self.active and not (self.is_waiting_spam_key or self.is_waiting_toggle_key):
                if keyboard.is_pressed(self.key_spam):
                    self.update_ui("Статус: ЗАЛИВАЕМ!", "green")
                    while keyboard.is_pressed(self.key_spam) and self.active:
                        keyboard.write(self.key_spam) 
                        time.sleep(0.05)
                    self.update_ui(f"Статус: ОЖИДАНИЕ ({self.key_spam.upper()})", "blue")
            time.sleep(0.01)

if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateClicker(root)
    root.mainloop()
