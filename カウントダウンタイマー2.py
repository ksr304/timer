import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import threading
import pygame
import os
import json
import sys
from PIL import Image, ImageTk, ImageEnhance

class TimerAlarmApp:
    def __init__(self, master):
        self.master = master
        master.title("タイマーアラーム")
        master.attributes('-fullscreen', True)
        master.configure(bg='black')

        self.style = ttk.Style()
        self.style.configure('TLabel', foreground='white', background='black', font=('Noto Serif CJK JP Black', 12))
        self.style.configure('TButton', font=('Noto Serif CJK JP Black', 12))
        self.style.configure('TFrame', background='black')

        self.main_timer = tk.StringVar(value="0")
        self.alarm_times = [tk.StringVar(value="0") for _ in range(2)]
        self.sound_files = [tk.StringVar() for _ in range(3)]  # カウントアップ用のサウンドファイルを削除
        self.image_file = tk.StringVar()
        self.sub1_image_file = tk.StringVar()

        self.settings_frame = ttk.Frame(master, style='TFrame')
        self.countdown_frame = ttk.Frame(master, style='TFrame')
        self.image_frame = ttk.Frame(master, style='TFrame')

        self.load_settings()
        self.create_settings_widgets()
        self.create_countdown_widgets()
        self.create_image_widgets()

        self.settings_frame.pack(fill='both', expand=True)

        pygame.mixer.init()
        self.running = False
        self.paused = False
        self.remaining_time = 0
        self.initial_time = 0
        self.count_up_time = 0
        self.count_up_running = False

        self.numpad = None

    def create_settings_widgets(self):
        ttk.Label(self.settings_frame, text="メインアラーム設定（分）:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.main_timer_entry = ttk.Entry(self.settings_frame, textvariable=self.main_timer, width=10)
        self.main_timer_entry.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        self.main_timer_entry.bind('<FocusIn>', self.show_numpad)

        for i in range(2):
            ttk.Label(self.settings_frame, text=f"サブアラーム{i+1}設定（設定時間後）:").grid(row=i+1, column=0, sticky='w', padx=10, pady=5)
            entry = ttk.Entry(self.settings_frame, textvariable=self.alarm_times[i], width=10)
            entry.grid(row=i+1, column=1, sticky='w', padx=10, pady=5)
            entry.bind('<FocusIn>', self.show_numpad)

        alarm_names = ["メイン", "サブ1", "サブ2"]
        for i in range(3):  # カウントアップアラームを削除
            ttk.Label(self.settings_frame, text=f"アラーム音{alarm_names[i]}:").grid(row=i+3, column=0, sticky='w', padx=10, pady=5)
            ttk.Button(self.settings_frame, text="選択", command=lambda i=i: self.select_file(self.sound_files[i], [("音声ファイル", "*.mp3 *.wav")])).grid(row=i+3, column=1, sticky='w', padx=5)
            ttk.Entry(self.settings_frame, textvariable=self.sound_files[i], width=50).grid(row=i+3, column=2, sticky='w', padx=10, pady=5)

        ttk.Label(self.settings_frame, text="メイン表示画像:").grid(row=6, column=0, sticky='w', padx=10, pady=5)
        ttk.Button(self.settings_frame, text="選択", command=lambda: self.select_file(self.image_file, [("画像ファイル", "*.png *.jpg *.jpeg *.gif")])).grid(row=6, column=1, sticky='w', padx=5)
        ttk.Entry(self.settings_frame, textvariable=self.image_file, width=50).grid(row=6, column=2, sticky='w', padx=10, pady=5)

        ttk.Label(self.settings_frame, text="サブ1表示画像:").grid(row=7, column=0, sticky='w', padx=10, pady=5)
        ttk.Button(self.settings_frame, text="選択", command=lambda: self.select_file(self.sub1_image_file, [("画像ファイル", "*.png *.jpg *.jpeg *.gif")])).grid(row=7, column=1, sticky='w', padx=5)
        ttk.Entry(self.settings_frame, textvariable=self.sub1_image_file, width=50).grid(row=7, column=2, sticky='w', padx=10, pady=5)

        start_button = tk.Button(self.settings_frame, text="スタート", command=self.start_timer, 
                                 bg='red', fg='white', font=('Noto Serif CJK JP Black', 20),
                                 width=20, height=2)
        start_button.grid(row=9, column=0, columnspan=2, pady=30, padx=20, sticky='w')

        exit_button = tk.Button(self.settings_frame, text="終了", command=self.exit_app,
                                bg='gray', fg='white', font=('Noto Serif CJK JP Black', 16),
                                width=10, height=1)
        exit_button.grid(row=9, column=1, columnspan=2, pady=30, padx=(100, 20), sticky='w')

    def show_numpad(self, event):
        if self.numpad:
            self.close_numpad()

        entry = event.widget
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()

        self.numpad = tk.Toplevel(self.master)
        self.numpad.wm_geometry(f"+{x}+{y}")
        self.numpad.title("テンキー")
        self.numpad.configure(bg='lightgray')
        self.numpad.protocol("WM_DELETE_WINDOW", self.close_numpad)
        self.numpad.transient(self.master)
        self.numpad.resizable(False, False)

        def button_click(number):
            current = entry.get()
            entry.delete(0, tk.END)
            entry.insert(0, current + str(number))

        def button_clear():
            entry.delete(0, tk.END)

        def button_enter():
            self.close_numpad()

        buttons = [
            '7', '8', '9',
            '4', '5', '6',
            '1', '2', '3',
            '0', 'C', 'Enter'
        ]

        for i, button in enumerate(buttons):
            row, col = divmod(i, 3)
            if button == 'C':
                cmd = button_clear
            elif button == 'Enter':
                cmd = button_enter
            else:
                cmd = lambda x=button: button_click(x)
            
            tk.Button(self.numpad, text=button, command=cmd, width=5, height=2).grid(row=row, column=col, padx=2, pady=2)

        self.numpad.bind("<FocusOut>", lambda e: self.close_numpad())
        self.numpad.focus_set()

    def close_numpad(self):
        if self.numpad:
            self.numpad.destroy()
            self.numpad = None
        self.master.focus_set()

    def create_countdown_widgets(self):
        self.time_label = tk.Label(self.countdown_frame, text="", font=('Noto Serif CJK JP Black', 120), bg='black', fg='white')
        self.time_label.pack(expand=True)

        button_frame = ttk.Frame(self.countdown_frame, style='TFrame')
        button_frame.pack(side='bottom', pady=10)

        self.pause_button = ttk.Button(button_frame, text="一時停止", command=self.pause_resume_timer, style='TButton')
        self.pause_button.pack(side='left', padx=10)

        self.end_button = ttk.Button(button_frame, text="終了", command=self.end_timer, style='TButton')
        self.end_button.pack(side='left', padx=10)

    def create_image_widgets(self):
        self.image_label = tk.Label(self.image_frame, bg='black')
        self.image_label.pack(fill='both', expand=True)

    def select_file(self, variable, filetypes):
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            variable.set(filename)

    def start_timer(self):
        try:
            self.initial_time = int(self.main_timer.get()) * 60
            alarm_times = [self.initial_time - int(t.get()) * 60 for t in self.alarm_times]

            self.settings_frame.pack_forget()
            self.countdown_frame.pack(fill='both', expand=True)

            self.master.update()

            screen_width = self.master.winfo_width()
            screen_height = self.master.winfo_height()
            font_size = min(screen_width // 4, screen_height // 2)
            self.time_label.configure(font=('Noto Serif CJK JP Black', font_size))

            button_frame = self.pause_button.master
            button_frame.pack_forget()
            button_frame.pack(side='bottom', pady=10)  # デフォルトの余白を使用

            self.running = True
            self.paused = False
            self.remaining_time = self.initial_time
            self.timer_thread = threading.Thread(target=self.run_timer, args=(alarm_times,), daemon=True)
            self.timer_thread.start()

            self.save_settings()
        except ValueError:
            messagebox.showerror("エラー", "無効な入力です。数値を入力してください。")

    def pause_resume_timer(self):
        self.paused = not self.paused
        self.pause_button.config(text="再開" if self.paused else "一時停止")

    def end_timer(self):
        self.running = False
        self.paused = False
        self.count_up_running = False
        self.countdown_frame.pack_forget()
        self.image_frame.pack_forget()
        self.settings_frame.pack(fill='both', expand=True)

    def run_timer(self, alarm_times):
        start_time = time.time()
        total_pause_time = 0
        pause_start_time = None
        sub1_shown = False

        while self.running:
            current_time = time.time()
            
            if self.paused:
                if pause_start_time is None:
                    pause_start_time = current_time
            else:
                if pause_start_time is not None:
                    total_pause_time += current_time - pause_start_time
                    pause_start_time = None
                
                elapsed_time = current_time - start_time - total_pause_time
                
                if self.remaining_time > 0:
                    self.remaining_time = max(0, int(self.initial_time - elapsed_time))
                    minutes, seconds = divmod(self.remaining_time, 60)
                    self.master.after_idle(self.update_time_label, f"{minutes:02d}:{seconds:02d}")
                    
                    if self.remaining_time == 0:
                        self.master.after_idle(self.play_sound_thread, self.sound_files[0].get())
                        self.master.after_idle(lambda: self.show_fade_in_image(self.image_file.get(), True, False))
                        self.count_up_running = True
                    
                    for i, alarm_time in enumerate(alarm_times):
                        if self.remaining_time == alarm_time:
                            self.master.after_idle(self.play_sound_thread, self.sound_files[i+1].get())
                            if i == 0 and not sub1_shown:
                                self.master.after_idle(lambda: self.show_fade_in_image(self.sub1_image_file.get(), False, True))
                                sub1_shown = True
                else:
                    # カウントアップ
                    self.count_up_time = int(elapsed_time - self.initial_time)
                    minutes, seconds = divmod(self.count_up_time, 60)
                    self.master.after_idle(self.update_time_label, f"+{minutes:02d}:{seconds:02d}")
            
            time.sleep(0.1)

    def update_time_label(self, time_str):
        self.time_label.config(text=time_str)

    def show_fade_in_image(self, image_file, is_final, fast_fade=False):
        if not image_file:
            return

        self.countdown_frame.pack_forget()
        self.image_frame.pack(fill='both', expand=True)

        image = Image.open(image_file)
        image = image.resize((self.master.winfo_width(), self.master.winfo_height()), Image.Resampling.LANCZOS)

        steps = 5 if fast_fade else 21
        sleep_time = 0.02 if fast_fade else 0.1

        for i in range(steps):
            alpha = i / (steps - 1)
            enhancer = ImageEnhance.Brightness(image)
            faded_image = enhancer.enhance(alpha)
            photo = ImageTk.PhotoImage(faded_image)
            self.image_label.config(image=photo)
            self.image_label.image = photo
            self.master.update()
            time.sleep(sleep_time)

        if is_final:
            self.master.after(5000, self.end_timer)
        else:
            self.master.after(3000, self.show_countdown)

    def show_countdown(self):
        self.image_frame.pack_forget()
        self.countdown_frame.pack(fill='both', expand=True)

    def play_sound_thread(self, sound_file):
        threading.Thread(target=self.play_sound, args=(sound_file,), daemon=True).start()

    def play_sound(self, sound_file):
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
            time.sleep(3)
            pygame.mixer.music.stop()
        except pygame.error:
            print(f"音声ファイルの読み込みに失敗しました: {sound_file}")

    def save_settings(self):
        settings = {
            'main_timer': self.main_timer.get(),
            'alarm_times': [t.get() for t in self.alarm_times],
            'sound_files': [s.get() for s in self.sound_files],
            'image_file': self.image_file.get(),
            'sub1_image_file': self.sub1_image_file.get()
        }
        with open('timer_settings.json', 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open('timer_settings.json', 'r') as f:
                settings = json.load(f)
            self.main_timer.set(settings['main_timer'])
            for i, t in enumerate(settings['alarm_times']):
                self.alarm_times[i].set(t)
            for i, s in enumerate(settings['sound_files']):
                self.sound_files[i].set(s)
            self.image_file.set(settings['image_file'])
            self.sub1_image_file.set(settings.get('sub1_image_file', ''))
        except FileNotFoundError:
            pass

    def exit_app(self):
        if messagebox.askokcancel("終了", "アプリケーションを終了しますか？"):
            self.master.quit()
            self.master.destroy()
            sys.exit()

if __name__ == "__main__":
    root = tk.Tk()
    app = TimerAlarmApp(root)
    root.mainloop()