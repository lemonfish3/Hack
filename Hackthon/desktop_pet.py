import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import datetime
from tkcalendar import Calendar
import json
import os
import time
import math
from pynput import mouse

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
        self.pet_label.bind('<Button-1>', self.show_menu)  # 左键点击显示菜单
        self.pet_label.bind('<B1-Motion>', self.drag)      # 左键拖动
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
        
        # 初始化移动相关变量
        self.target_x = None
        self.target_y = None
        self.move_speed = 5  # 移动速度（像素/帧）
        self.is_moving = False
        
        # print("正在初始化全局点击事件...")
        # 启动全局鼠标监听
        self.mouse_listener = mouse.Listener(on_click=self.on_global_click)
        self.mouse_listener.start()
        # print("全局点击事件初始化完成")
        
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
    
    def on_global_click(self, x, y, button, pressed):
        """处理全局鼠标点击事件"""
        if not pressed or button != mouse.Button.left:
            return
            
        # print(f"检测到全局点击: x={x}, y={y}")
        
        # 如果正在移动，不处理新的点击
        if self.is_moving:
            # print("宠物正在移动中")
            return
        
        # 设置目标位置（考虑窗口大小，使点击位置成为宠物中心）
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        self.target_x = x - window_width // 2
        self.target_y = y - window_height // 2
        
        # print(f"目标位置: x={self.target_x}, y={self.target_y}")
        # print(f"窗口大小: width={window_width}, height={window_height}")
        
        # 开始移动
        self.move_to_target()
    
    def move_to_target(self):
        """移动到目标位置"""
        if self.target_x is None or self.target_y is None:
            return
        
        self.is_moving = True
        
        # 获取窗口当前位置
        window_x = self.window.winfo_x()
        window_y = self.window.winfo_y()
        
        # 计算到目标位置的距离
        dx = self.target_x - window_x
        dy = self.target_y - window_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # print(f"当前位置: x={window_x}, y={window_y}")
        # print(f"移动距离: {distance:.2f}像素")
        
        if distance > 0:
            # 设置移动动画
            self.current_state = 'moving'
            self.animation_frames = self.animations['moving']
            
            # 计算移动步长
            step = min(self.move_speed, distance)
            ratio = step / distance
            
            # 计算新位置
            new_x = window_x + int(dx * ratio)
            new_y = window_y + int(dy * ratio)
            
            # print(f"下一步位置: x={new_x}, y={new_y}")
            
            # 移动窗口
            self.window.geometry(f'+{new_x}+{new_y}')
            
            # 如果还没到达目标位置，继续移动
            if distance > self.move_speed:
                self.window.after(50, self.move_to_target)
            else:
                # 到达目标位置，清除目标并恢复idle状态
                # print("到达目标位置")
                self.target_x = None
                self.target_y = None
                self.is_moving = False
                self.window.after(100, lambda: self.set_idle_state())
        else:
            # print("已经在目标位置")
            self.is_moving = False
            self.set_idle_state()
    
    def set_idle_state(self):
        """设置idle状态"""
        self.current_state = 'idle'
        self.animation_frames = self.animations['idle']
        self.is_moving = False
    
    def load_data(self):
        """加载保存的数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
                # Convert old format reminders to new format if needed
                if self.data['reminders'] and isinstance(self.data['reminders'][0], str):
                    self.data['reminders'] = [{'text': text, 'completed': False} for text in self.data['reminders']]
        else:
            self.data = {
                'notes': [],
                'period_records': [],
                'reminders': []  # Each reminder will be a dict with 'text' and 'completed' fields
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
        self.menu.add_command(label='设置', command=self.show_settings)
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
        reminder_window.geometry('400x500')  # Set a fixed size for the window
        
        # Create main container with scrollbar
        main_container = tk.Frame(reminder_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create a frame for the list of reminders
        list_frame = tk.Frame(scrollable_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Display existing reminders
        if not self.data['reminders']:
            empty_frame = tk.Frame(list_frame)
            empty_frame.pack(fill='x', pady=2)
            tk.Label(empty_frame, text="暂无提醒事项", fg='gray').pack()
        else:
            for i, reminder in enumerate(self.data['reminders']):
                reminder_frame = tk.Frame(list_frame)
                reminder_frame.pack(fill='x', pady=2)
                
                # Create checkbox
                completed = tk.BooleanVar(value=reminder.get('completed', False))
                checkbox = tk.Checkbutton(reminder_frame, variable=completed,
                                        command=lambda idx=i, var=completed: self.update_reminder_status(idx, var.get()))
                checkbox.pack(side='left', padx=(0, 5))
                
                # Create label with strikethrough if completed
                reminder_label = tk.Label(reminder_frame, text=reminder['text'], wraplength=300)
                if completed.get():
                    reminder_label.config(font=('TkDefaultFont', 9, 'overstrike'))
                reminder_label.pack(side='left', fill='x', expand=True)
                
                # Create delete button
                delete_btn = tk.Button(reminder_frame, text='删除', 
                                     command=lambda idx=i, f=reminder_frame: self.delete_reminder(idx, f))
                delete_btn.pack(side='right', padx=(5, 0))
        
        # Add separator
        ttk.Separator(reminder_window, orient='horizontal').pack(fill='x', pady=10)
        
        # Create frame for adding new reminders
        input_frame = tk.Frame(reminder_window)
        input_frame.pack(pady=10, padx=10, fill='x')
        
        content = tk.StringVar()
        entry = tk.Entry(input_frame, textvariable=content, width=40)
        entry.pack(side='left', padx=(0, 5))
        
        def add_reminder():
            text = content.get().strip()
            if text:
                new_reminder = {'text': text, 'completed': False}
                self.data['reminders'].append(new_reminder)
                self.save_data()
                
                # 如果这是第一个提醒事项，清除"暂无提醒事项"的提示
                if len(self.data['reminders']) == 1:
                    for widget in list_frame.winfo_children():
                        widget.destroy()
                
                # Add new reminder to the list
                reminder_frame = tk.Frame(list_frame)
                reminder_frame.pack(fill='x', pady=2)
                
                completed = tk.BooleanVar(value=False)
                checkbox = tk.Checkbutton(reminder_frame, variable=completed,
                                        command=lambda idx=len(self.data['reminders'])-1, var=completed: 
                                        self.update_reminder_status(idx, var.get()))
                checkbox.pack(side='left', padx=(0, 5))
                
                reminder_label = tk.Label(reminder_frame, text=text, wraplength=300)
                reminder_label.pack(side='left', fill='x', expand=True)
                
                delete_btn = tk.Button(reminder_frame, text='删除',
                                     command=lambda idx=len(self.data['reminders'])-1, f=reminder_frame: 
                                     self.delete_reminder(idx, f))
                delete_btn.pack(side='right', padx=(5, 0))
                
                # Clear the entry
                content.set('')
                # Scroll to the bottom
                canvas.yview_moveto(1.0)
        
        add_button = tk.Button(input_frame, text='添加提醒', command=add_reminder)
        add_button.pack(side='left')
        
        # Bind Enter key to add reminder
        entry.bind('<Return>', lambda e: add_reminder())
    
    def update_reminder_status(self, index, completed):
        """更新提醒事项的完成状态"""
        self.data['reminders'][index]['completed'] = completed
        self.save_data()
    
    def delete_reminder(self, index, frame):
        """删除提醒事项"""
        # 从数据中删除
        self.data['reminders'].pop(index)
        self.save_data()
        
        # 销毁当前frame
        frame.destroy()
        
        # 如果删除后没有提醒事项了，显示提示
        if not self.data['reminders']:
            # 创建一个新的frame来显示提示
            empty_frame = tk.Frame(frame.master)
            empty_frame.pack(fill='x', pady=2)
            tk.Label(empty_frame, text="暂无提醒事项", fg='gray').pack()
    
    def notepad(self):
        """记事本功能"""
        notepad_window = tk.Toplevel(self.window)
        notepad_window.title('记事本')
        notepad_window.geometry('400x500')
        
        # Create main container with scrollbar
        main_container = tk.Frame(notepad_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create a frame for the list of notes
        list_frame = tk.Frame(scrollable_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Display existing notes
        if not self.data['notes']:
            empty_frame = tk.Frame(list_frame)
            empty_frame.pack(fill='x', pady=2)
            tk.Label(empty_frame, text="暂无笔记", fg='gray').pack()
        else:
            for i, note in enumerate(self.data['notes']):
                note_frame = tk.Frame(list_frame)
                note_frame.pack(fill='x', pady=2)
                
                note_text = tk.Text(note_frame, height=3, width=40, wrap=tk.WORD)
                note_text.insert('1.0', note)
                note_text.config(state='disabled')  # Make text read-only
                note_text.pack(side='left', padx=(0, 5))
                
                # Create delete button
                delete_btn = tk.Button(note_frame, text='删除',
                                     command=lambda idx=i, f=note_frame: self.delete_note(idx, f))
                delete_btn.pack(side='right', padx=(5, 0))
        
        # Add separator
        ttk.Separator(notepad_window, orient='horizontal').pack(fill='x', pady=10)
        
        # Create frame for adding new notes
        input_frame = tk.Frame(notepad_window)
        input_frame.pack(pady=10, padx=10, fill='x')
        
        text_widget = tk.Text(input_frame, height=3, width=40)
        text_widget.pack(side='left', padx=(0, 5))
        
        def save_note():
            note = text_widget.get('1.0', tk.END).strip()
            if note:
                self.data['notes'].append(note)
                self.save_data()
                
                # 如果这是第一个笔记，清除"暂无笔记"的提示
                if len(self.data['notes']) == 1:
                    for widget in list_frame.winfo_children():
                        widget.destroy()
                
                # Add new note to the list
                note_frame = tk.Frame(list_frame)
                note_frame.pack(fill='x', pady=2)
                
                note_text = tk.Text(note_frame, height=3, width=40, wrap=tk.WORD)
                note_text.insert('1.0', note)
                note_text.config(state='disabled')  # Make text read-only
                note_text.pack(side='left', padx=(0, 5))
                
                delete_btn = tk.Button(note_frame, text='删除',
                                     command=lambda idx=len(self.data['notes'])-1, f=note_frame: 
                                     self.delete_note(idx, f))
                delete_btn.pack(side='right', padx=(5, 0))
                
                # Clear the input
                text_widget.delete('1.0', tk.END)
                # Scroll to the bottom
                canvas.yview_moveto(1.0)
        
        save_button = tk.Button(input_frame, text='保存', command=save_note)
        save_button.pack(side='left')
    
    def delete_note(self, index, frame):
        """删除笔记"""
        # 从数据中删除
        self.data['notes'].pop(index)
        self.save_data()
        
        # 销毁当前frame
        frame.destroy()
        
        # 如果删除后没有笔记了，显示提示
        if not self.data['notes']:
            # 创建一个新的frame来显示提示
            empty_frame = tk.Frame(frame.master)
            empty_frame.pack(fill='x', pady=2)
            tk.Label(empty_frame, text="暂无笔记", fg='gray').pack()
    
    def show_settings(self):
        """显示设置窗口"""
        settings_window = tk.Toplevel(self.window)
        settings_window.title('设置')
        settings_window.geometry('300x200')
        
        # 创建速度设置框架
        speed_frame = tk.Frame(settings_window)
        speed_frame.pack(pady=20, padx=20, fill='x')
        
        tk.Label(speed_frame, text='移动速度:').pack(side='left')
        
        speed_var = tk.IntVar(value=self.move_speed)
        speed_scale = tk.Scale(speed_frame, from_=1, to=20, orient='horizontal',
                             variable=speed_var, length=200)
        speed_scale.pack(side='left', padx=10)
        
        def apply_settings():
            self.move_speed = speed_var.get()
            settings_window.destroy()
        
        # 应用按钮
        tk.Button(settings_window, text='应用', command=apply_settings).pack(pady=20)
    
    def run(self):
        """运行桌宠程序"""
        try:
            self.window.mainloop()
        finally:
            # 确保在程序退出时停止鼠标监听
            if hasattr(self, 'mouse_listener'):
                self.mouse_listener.stop()

if __name__ == '__main__':
    pet = DesktopPet()
    pet.run() 