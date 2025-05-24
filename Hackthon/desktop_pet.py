import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import datetime
from tkcalendar import Calendar
import json
import os
import time
import math

class DesktopPet:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('Desktop Pet')
        
        # 设置窗口透明
        self.window.attributes('-alpha', 0.9)
        # 移除窗口边框
        self.window.overrideredirect(True)
        # 设置窗口置顶
        self.window.attributes('-topmost', True)
        
        # 加载GIF动画
        self.load_animations()
        
        # 创建标签显示动画
        self.pet_label = tk.Label(self.window)
        self.pet_label.pack()
        
        # 设置当前动画状态
        self.current_state = 'idle'
        self.animation_frames = self.animations['idle']
        self.current_frame = 0
        
        # 绑定鼠标事件
        self.pet_label.bind('<Button-1>', self.show_menu)
        self.pet_label.bind('<B1-Motion>', self.drag)
        self.pet_label.bind('<Enter>', self.on_mouse_enter)
        self.pet_label.bind('<Leave>', self.on_mouse_leave)
        
        # 初始化功能菜单
        self.create_menu()
        
        # 存储鼠标位置
        self.x = 0
        self.y = 0
        
        # 初始化数据存储
        self.data_file = 'pet_data.json'
        self.load_data()
        
        # 开始动画循环
        self.animate()
    
    def load_animations(self):
        """加载所有动画状态的GIF"""
        self.animations = {
            'idle': self.load_gif('idle.gif'),
            'happy': self.load_gif('happy.gif'),
            'moving': self.load_gif('moving.gif')
        }
    
    def load_gif(self, filename):
        """加载GIF文件并返回帧列表"""
        try:
            gif = Image.open(filename)
            frames = []
            try:
                while True:
                    frames.append(ImageTk.PhotoImage(gif.copy()))
                    gif.seek(len(frames))
            except EOFError:
                pass
            return frames
        except FileNotFoundError:
            # 如果找不到GIF文件，返回默认图像
            default_img = Image.new('RGBA', (100, 100), 'white')
            return [ImageTk.PhotoImage(default_img)]
    
    def animate(self):
        """更新动画帧"""
        if self.animation_frames:
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)
            self.pet_label.configure(image=self.animation_frames[self.current_frame])
        self.window.after(100, self.animate)  # 每100ms更新一次
    
    def on_mouse_enter(self, event):
        """鼠标悬停时的动作"""
        self.current_state = 'happy'
        self.animation_frames = self.animations['happy']
        self.current_frame = 0
    
    def on_mouse_leave(self, event):
        """鼠标离开时的动作"""
        self.current_state = 'idle'
        self.animation_frames = self.animations['idle']
        self.current_frame = 0
    
    def follow_mouse(self):
        """让桌宠跟随鼠标移动"""
        if self.current_state != 'moving':
            # 获取鼠标和窗口位置
            mouse_x = self.window.winfo_pointerx()
            mouse_y = self.window.winfo_pointery()
            window_x = self.window.winfo_x()
            window_y = self.window.winfo_y()
            
            # 计算距离
            distance = math.sqrt((mouse_x - window_x)**2 + (mouse_y - window_y)**2)
            
            # 如果鼠标离桌宠较远，则移动
            if distance > 100:
                # 计算移动方向
                dx = (mouse_x - window_x) / distance * 5
                dy = (mouse_y - window_y) / distance * 5
                
                # 更新位置
                new_x = window_x + int(dx)
                new_y = window_y + int(dy)
                
                # 设置移动动画
                self.current_state = 'moving'
                self.animation_frames = self.animations['moving']
                
                # 移动窗口
                self.window.geometry(f'+{new_x}+{new_y}')
            elif self.current_state == 'moving':
                # 停止移动时恢复idle状态
                self.current_state = 'idle'
                self.animation_frames = self.animations['idle']
        
        # 继续检查鼠标位置
        self.window.after(50, self.follow_mouse)
    
    def load_data(self):
        """加载保存的数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {
                'notes': [],
                'period_records': [],
                'reminders': []
            }
    
    def save_data(self):
        """保存数据到文件"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f)
    
    def create_menu(self):
        """创建功能菜单"""
        self.menu = tk.Menu(self.window, tearoff=0)
        self.menu.add_command(label='经期记录', command=self.period_tracker)
        self.menu.add_command(label='计时器', command=self.timer)
        self.menu.add_command(label='提醒事项', command=self.reminder)
        self.menu.add_command(label='记事本', command=self.notepad)
        self.menu.add_separator()
        self.menu.add_command(label='退出', command=self.window.quit)
    
    def show_menu(self, event):
        """显示菜单"""
        self.menu.post(event.x_root, event.y_root)
    
    def drag(self, event):
        """实现拖动功能"""
        new_x = self.window.winfo_x() + (event.x_root - self.x)
        new_y = self.window.winfo_y() + (event.y_root - self.y)
        self.window.geometry(f'+{new_x}+{new_y}')
        self.x = event.x_root
        self.y = event.y_root
    
    def period_tracker(self):
        """经期记录功能"""
        tracker_window = tk.Toplevel(self.window)
        tracker_window.title('经期记录')
        
        cal = Calendar(tracker_window)
        cal.pack(pady=10)
        
        def record_date():
            selected_date = cal.get_date()
            self.data['period_records'].append(selected_date)
            self.save_data()
            tk.Label(tracker_window, text=f'已记录: {selected_date}').pack()
        
        tk.Button(tracker_window, text='记录这一天', command=record_date).pack()
    
    def timer(self):
        """计时器功能"""
        timer_window = tk.Toplevel(self.window)
        timer_window.title('计时器')
        
        minutes = tk.StringVar(value='25')
        tk.Entry(timer_window, textvariable=minutes).pack()
        
        time_label = tk.Label(timer_window, text='00:00')
        time_label.pack()
        
        def start_timer():
            try:
                mins = int(minutes.get())
                self.countdown(mins * 60, time_label)
            except ValueError:
                time_label.config(text='请输入有效数字')
        
        tk.Button(timer_window, text='开始', command=start_timer).pack()
    
    def countdown(self, seconds, label):
        """倒计时功能"""
        def count():
            nonlocal seconds
            if seconds > 0:
                mins, secs = divmod(seconds, 60)
                label.config(text=f'{mins:02d}:{secs:02d}')
                seconds -= 1
                label.after(1000, count)
            else:
                label.config(text='时间到！')
        
        count()
    
    def reminder(self):
        """提醒事项功能"""
        reminder_window = tk.Toplevel(self.window)
        reminder_window.title('提醒事项')
        
        content = tk.StringVar()
        tk.Entry(reminder_window, textvariable=content).pack()
        
        def add_reminder():
            text = content.get()
            if text:
                self.data['reminders'].append(text)
                self.save_data()
                tk.Label(reminder_window, text=f'已添加提醒: {text}').pack()
        
        tk.Button(reminder_window, text='添加提醒', command=add_reminder).pack()
    
    def notepad(self):
        """记事本功能"""
        notepad_window = tk.Toplevel(self.window)
        notepad_window.title('记事本')
        
        text_widget = tk.Text(notepad_window, height=10, width=40)
        text_widget.pack()
        
        def save_note():
            note = text_widget.get('1.0', tk.END).strip()
            if note:
                self.data['notes'].append(note)
                self.save_data()
                tk.Label(notepad_window, text='笔记已保存').pack()
        
        tk.Button(notepad_window, text='保存', command=save_note).pack()
    
    def run(self):
        """运行桌宠程序"""
        self.follow_mouse()  # 启动鼠标跟随
        self.window.mainloop()

if __name__ == '__main__':
    pet = DesktopPet()
    pet.run() 