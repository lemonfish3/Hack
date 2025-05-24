import sys
import signal
from PySide6.QtWidgets import (QApplication, QLabel, QWidget, QMenu, QSystemTrayIcon,
                              QCalendarWidget, QInputDialog, QMessageBox, QDialog,
                              QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox, QLineEdit,
                              QScrollArea, QFrame, QCheckBox, QTextEdit, QMainWindow, QTabWidget)
from PySide6.QtCore import Qt, QPoint, QTimer, QDateTime, QTime, QSize
from PySide6.QtGui import QMovie, QMouseEvent, QCursor, QAction, QFont, QPalette, QColor, QIcon
import json
import os
from datetime import datetime, timedelta
from ui_style import apply_purple_theme  # Import the UI styling
from pathlib import Path

# 确保数据目录存在
DATA_DIR = os.path.join(os.path.expanduser('~'), '.desktop_pet')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class ScrollableDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle(title)
        self.setMinimumSize(400, 500)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        scroll.setWidget(self.content_widget)

class ReminderDialog(ScrollableDialog):
    def __init__(self, parent=None):
        super().__init__("Reminders", parent)
        self.parent_widget = parent
        
        # List frame for reminders
        self.list_frame = QFrame()
        self.list_layout = QVBoxLayout(self.list_frame)
        self.content_layout.addWidget(self.list_frame)
        
        # Input frame for new reminder
        input_frame = QFrame()
        input_layout = QVBoxLayout(input_frame)
        
        # Text input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter reminder text...")
        input_layout.addWidget(self.text_input)
        
        # Date and time inputs
        datetime_frame = QFrame()
        datetime_layout = QHBoxLayout(datetime_frame)
        
        self.date_edit = QCalendarWidget()
        datetime_layout.addWidget(self.date_edit)
        
        time_frame = QFrame()
        time_layout = QVBoxLayout(time_frame)
        
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setPrefix("Hour: ")
        time_layout.addWidget(self.hour_spin)
        
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setPrefix("Minute: ")
        time_layout.addWidget(self.minute_spin)
        
        datetime_layout.addWidget(time_frame)
        input_layout.addWidget(datetime_frame)
        
        # Add button
        add_button = QPushButton("Add Reminder")
        add_button.clicked.connect(self.add_reminder)
        input_layout.addWidget(add_button)
        
        self.content_layout.addWidget(input_frame)
        
        # Load existing reminders
        self.load_reminders()
    
    def load_reminders(self):
        reminders = self.parent_widget.data['reminders'] if hasattr(self.parent_widget, 'data') else []
        if not reminders:
            label = QLabel("No reminders")
            label.setStyleSheet("color: gray;")
            self.list_layout.addWidget(label)
        else:
            # Sort reminders by datetime
            reminders.sort(key=lambda x: x.get('datetime', ''))
            for reminder in reminders:
                self.add_reminder_widget(reminder)
    
    def add_reminder(self):
        text = self.text_input.text().strip()
        if text:
            # Get selected date and time
            selected_date = self.date_edit.selectedDate()
            hour = self.hour_spin.value()
            minute = self.minute_spin.value()
            
            # Create datetime string
            reminder_datetime = datetime.combine(
                selected_date.toPython(),
                datetime.min.time().replace(hour=hour, minute=minute)
            ).strftime("%Y-%m-%d %H:%M:%S")
            
            reminder = {
                'text': text,
                'datetime': reminder_datetime,
                'completed': False
            }
            
            self.parent_widget.data['reminders'].append(reminder)
            self.parent_widget.save_data()
            
            # Clear inputs
            self.text_input.clear()
            self.hour_spin.setValue(0)
            self.minute_spin.setValue(0)
            
            # Clear existing reminders and reload
            while self.list_layout.count():
                item = self.list_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            self.load_reminders()
            
            QMessageBox.information(self, "Success", "Reminder added successfully!")
    
    def add_reminder_widget(self, reminder):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        
        # Show datetime and text
        datetime_str = reminder.get('datetime', '')
        text = reminder.get('text', '')
        label = QLabel(f"{datetime_str}\n{text}")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.delete_reminder(reminder, frame))
        layout.addWidget(delete_btn)
        
        self.list_layout.addWidget(frame)
    
    def delete_reminder(self, reminder, frame):
        if reminder in self.parent_widget.data['reminders']:
            self.parent_widget.data['reminders'].remove(reminder)
            self.parent_widget.save_data()
            frame.deleteLater()
            
            # Show "No reminders" if list is empty
            if not self.parent_widget.data['reminders']:
                label = QLabel("No reminders")
                label.setStyleSheet("color: gray;")
                self.list_layout.addWidget(label)

class NotesDialog(QDialog):
    def __init__(self, notes, parent=None):
        super().__init__(parent)
        self.notes = notes
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Notes")
        layout = QVBoxLayout(self)
        
        # Note input
        self.note_input = QTextEdit()
        layout.addWidget(QLabel("New Note:"))
        layout.addWidget(self.note_input)
        
        # Add note button
        add_button = QPushButton("Add Note")
        add_button.clicked.connect(self.add_note)
        layout.addWidget(add_button)
        
        # Notes list
        layout.addWidget(QLabel("Your Notes:"))
        self.notes_list = QTextEdit()
        self.notes_list.setReadOnly(True)
        self.update_notes()
        layout.addWidget(self.notes_list)
        
        # Delete button
        delete_button = QPushButton("Delete Selected Note")
        delete_button.clicked.connect(self.delete_note)
        layout.addWidget(delete_button)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
    def add_note(self):
        note_text = self.note_input.toPlainText().strip()
        if note_text:
            self.notes.append({
                'text': note_text,
                'date': datetime.now().isoformat()
            })
            self.note_input.clear()
            self.update_notes()
            
    def delete_note(self):
        selected_text = self.notes_list.textCursor().selectedText()
        if not selected_text:
            QMessageBox.warning(self, "No Selection", "Please select a note to delete.")
            return
            
        reply = QMessageBox.question(
            self, 'Delete Note',
            'Are you sure you want to delete this note?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for i, note in enumerate(self.notes):
                if note['text'] in selected_text:
                    del self.notes[i]
                    self.update_notes()
                    break
                    
    def update_notes(self):
        notes_text = ""
        for note in sorted(self.notes, key=lambda x: x['date'], reverse=True):
            date = datetime.fromisoformat(note['date']).strftime('%Y-%m-%d %H:%M')
            notes_text += f"[{date}]\n{note['text']}\n\n"
        self.notes_list.setText(notes_text)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)  # 使用独立窗口
        self.setWindowTitle('Settings')
        layout = QVBoxLayout()
        
        # Mouse following setting
        follow_layout = QHBoxLayout()
        self.follow_checkbox = QCheckBox("Enable Mouse Following")
        self.follow_checkbox.setChecked(parent.follow_mouse if parent else True)
        follow_layout.addWidget(self.follow_checkbox)
        layout.addLayout(follow_layout)
        
        # Speed setting
        speed_layout = QHBoxLayout()
        self.speed_input = QSpinBox()
        self.speed_input.setRange(1, 20)
        self.speed_input.setValue(parent.move_speed if parent else 5)
        speed_layout.addWidget(QLabel("Movement Speed:"))
        speed_layout.addWidget(self.speed_input)
        layout.addLayout(speed_layout)
        
        # OK button
        ok_button = QPushButton('Apply')
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        
        self.setLayout(layout)

class PeriodDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.parent_widget = parent
        self.setWindowTitle("Period Tracking")
        self.setMinimumSize(800, 600)  # Increased width to accommodate both calendars
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Date selection frame
        date_frame = QFrame()
        date_layout = QHBoxLayout(date_frame)  # Changed to horizontal layout for side-by-side calendars
        date_layout.setSpacing(20)
        
        # Start date selection
        start_frame = QFrame()
        start_layout = QVBoxLayout(start_frame)
        start_date_label = QLabel("Start Date:")
        start_date_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #6A5ACD;")
        start_layout.addWidget(start_date_label)
        
        self.start_calendar = QCalendarWidget()
        self.start_calendar.setMinimumSize(350, 350)
        self.start_calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #E6E6FA;
                border: 1px solid #C8C8E6;
                border-radius: 5px;
            }
            QCalendarWidget QToolButton {
                color: #6A5ACD;
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #D8D8F0;
                border-radius: 3px;
            }
            QCalendarWidget QMenu {
                background-color: #E6E6FA;
                border: 1px solid #C8C8E6;
            }
            QCalendarWidget QSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #C8C8E6;
                border-radius: 3px;
                padding: 3px;
            }
        """)
        start_layout.addWidget(self.start_calendar)
        date_layout.addWidget(start_frame)
        
        # End date selection
        end_frame = QFrame()
        end_layout = QVBoxLayout(end_frame)
        end_date_label = QLabel("End Date:")
        end_date_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #6A5ACD;")
        end_layout.addWidget(end_date_label)
        
        self.end_calendar = QCalendarWidget()
        self.end_calendar.setMinimumSize(350, 350)
        self.end_calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #E6E6FA;
                border: 1px solid #C8C8E6;
                border-radius: 5px;
            }
            QCalendarWidget QToolButton {
                color: #6A5ACD;
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #D8D8F0;
                border-radius: 3px;
            }
            QCalendarWidget QMenu {
                background-color: #E6E6FA;
                border: 1px solid #C8C8E6;
            }
            QCalendarWidget QSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #C8C8E6;
                border-radius: 3px;
                padding: 3px;
            }
        """)
        end_layout.addWidget(self.end_calendar)
        date_layout.addWidget(end_frame)
        
        # Record button with styling
        record_button = QPushButton("Record Period")
        record_button.setStyleSheet("""
            QPushButton {
                background-color: #6A5ACD;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #5A4ABD;
            }
        """)
        record_button.clicked.connect(self.record_period)
        
        # Center the record button
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.addStretch()
        button_layout.addWidget(record_button)
        button_layout.addStretch()
        
        layout.addWidget(date_frame)
        layout.addWidget(button_frame)
        
        # History section
        history_frame = QFrame()
        history_layout = QVBoxLayout(history_frame)
        
        history_label = QLabel("History:")
        history_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #6A5ACD;")
        history_layout.addWidget(history_label)
        
        # Scrollable area for history
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #C8C8E6;
                border-radius: 5px;
                background-color: white;
            }
        """)
        history_layout.addWidget(scroll)
        
        history_widget = QWidget()
        self.history_layout = QVBoxLayout(history_widget)
        self.history_layout.setSpacing(10)
        scroll.setWidget(history_widget)
        
        layout.addWidget(history_frame)
        
        # Load history
        self.load_history()
    
    def load_history(self):
        records = self.parent_widget.data.get('period_records', [])
        if not records:
            label = QLabel("No records yet")
            label.setStyleSheet("color: gray; padding: 10px;")
            self.history_layout.addWidget(label)
        else:
            # Sort records by start date
            records.sort(key=lambda x: x['start_date'], reverse=True)
            for record in records:
                # Create a frame for each record
                record_frame = QFrame()
                record_frame.setStyleSheet("""
                    QFrame {
                        background-color: #F0F0FF;
                        border-radius: 5px;
                        padding: 5px;
                    }
                """)
                record_layout = QHBoxLayout(record_frame)
                
                # Date label with improved formatting
                label = QLabel(f"From {record['start_date']} to {record['end_date']}")
                label.setStyleSheet("color: #333; font-size: 13px;")
                record_layout.addWidget(label)
                
                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FF6B6B;
                        color: white;
                        border-radius: 3px;
                        padding: 5px 10px;
                    }
                    QPushButton:hover {
                        background-color: #FF5252;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, r=record: self.delete_record(r))
                record_layout.addWidget(delete_btn)
                
                self.history_layout.addWidget(record_frame)
    
    def delete_record(self, record):
        if record in self.parent_widget.data['period_records']:
            self.parent_widget.data['period_records'].remove(record)
            self.parent_widget.save_data()
            
            # Clear and reload history
            while self.history_layout.count():
                item = self.history_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            self.load_history()
            QMessageBox.information(self, "Success", "Record deleted successfully!")
    
    def record_period(self):
        start_date = self.start_calendar.selectedDate().toString("yyyy-MM-dd")
        end_date = self.end_calendar.selectedDate().toString("yyyy-MM-dd")
        
        # Validate dates
        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Dates", "Start date cannot be after end date!")
            return
        
        # Create new record
        new_record = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        # Initialize period_records if it doesn't exist
        if 'period_records' not in self.parent_widget.data:
            self.parent_widget.data['period_records'] = []
        
        # Add the new record
        self.parent_widget.data['period_records'].append(new_record)
        self.parent_widget.save_data()
        
        # Clear and reload history
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.load_history()
        QMessageBox.information(self, "Success", "Period recorded successfully!")

class DesktopPet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Initialize data directory
        self.data_dir = os.getenv('DESKTOP_PET_DATA', os.path.expanduser('~/.desktop_pet'))
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load settings
        self.settings = self.load_data('settings.json', {
            'pet_size': 100,
            'animation_speed': 100,
            'stay_on_top': True,
            'show_notifications': True
        })
        
        # Initialize animation states
        self.current_state = 'idle'
        self.animations = self.load_animations()
        
        # Setup UI
        self.setup_pet()
        self.setup_tray()
        self.setup_context_menu()
        
        # Load data
        self.periods = self.load_data('periods.json', [])
        self.notes = self.load_data('notes.json', [])
        self.reminders = self.load_data('reminders.json', [])
        
        # Setup timer for reminders
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # Check every minute
        
    def load_animations(self):
        """Load all animation states"""
        animations = {}
        for state in ['idle', 'happy', 'moving']:
            movie = QMovie(f"{state}.gif")
            if movie.isValid():
                movie.setScaledSize(QSize(self.settings['pet_size'], self.settings['pet_size']))
                movie.setSpeed(self.settings['animation_speed'])
                animations[state] = movie
        return animations
        
    def load_data(self, filename, default=None):
        try:
            with open(os.path.join(self.data_dir, filename), 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default if default is not None else {}
            
    def save_data(self, filename, data):
        with open(os.path.join(self.data_dir, filename), 'w') as f:
            json.dump(data, f)
            
    def setup_pet(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        
        # Pet animation
        self.movie_label = QLabel()
        self.movie_label.setAlignment(Qt.AlignCenter)
        self.change_animation('idle')
        
        layout.addWidget(self.movie_label)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Make window draggable
        self.old_pos = None
        self.movie_label.mousePressEvent = self.mousePressEvent
        self.movie_label.mouseMoveEvent = self.mouseMoveEvent
        
    def change_animation(self, state):
        """Change the pet's animation state"""
        if state in self.animations and state != self.current_state:
            self.current_state = state
            self.movie_label.setMovie(self.animations[state])
            self.animations[state].start()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.position().toPoint()
            self.change_animation('happy')  # Change animation when clicked
        elif event.button() == Qt.RightButton:
            self.context_menu.popup(event.globalPosition().toPoint())
            
    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos'):
            delta = event.position().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.position().toPoint()
            self.change_animation('moving')  # Change animation while moving
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None
            self.change_animation('idle')  # Return to idle animation
            
    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("idle.gif"))
        self.tray_icon.show()
        
        # Tray menu
        tray_menu = QMenu()
        
        period_action = QAction("Period Tracking", self)
        period_action.triggered.connect(self.show_period_tracker)
        tray_menu.addAction(period_action)
        
        notes_action = QAction("Notes", self)
        notes_action.triggered.connect(self.show_notes)
        tray_menu.addAction(notes_action)
        
        reminders_action = QAction("Reminders", self)
        reminders_action.triggered.connect(self.show_reminders)
        tray_menu.addAction(reminders_action)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
    def setup_context_menu(self):
        self.context_menu = QMenu(self)
        
        period_action = QAction("Period Tracking", self)
        period_action.triggered.connect(self.show_period_tracker)
        self.context_menu.addAction(period_action)
        
        notes_action = QAction("Notes", self)
        notes_action.triggered.connect(self.show_notes)
        self.context_menu.addAction(notes_action)
        
        reminders_action = QAction("Reminders", self)
        reminders_action.triggered.connect(self.show_reminders)
        self.context_menu.addAction(reminders_action)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        self.context_menu.addAction(settings_action)
        
    def show_period_tracker(self):
        dialog = PeriodTrackerDialog(self.periods, self)
        if dialog.exec_():
            self.periods = dialog.periods
            self.save_data('periods.json', self.periods)
            
    def show_notes(self):
        dialog = NotesDialog(self.notes, self)
        if dialog.exec_():
            self.notes = dialog.notes
            self.save_data('notes.json', self.notes)
            
    def show_reminders(self):
        dialog = RemindersDialog(self.reminders, self)
        if dialog.exec_():
            self.reminders = dialog.reminders
            self.save_data('reminders.json', self.reminders)
            
    def show_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_():
            self.settings = dialog.settings
            self.save_data('settings.json', self.settings)
            self.apply_settings()
            
    def apply_settings(self):
        # Update animation sizes and speeds
        for movie in self.animations.values():
            movie.setScaledSize(QSize(self.settings['pet_size'], self.settings['pet_size']))
            movie.setSpeed(self.settings['animation_speed'])
        
        if self.settings['stay_on_top']:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
        
    def check_reminders(self):
        now = datetime.now()
        for reminder in self.reminders:
            reminder_time = datetime.fromisoformat(reminder['time'])
            if not reminder['notified'] and now >= reminder_time:
                if self.settings['show_notifications']:
                    self.tray_icon.showMessage(
                        "Reminder",
                        reminder['text'],
                        QSystemTrayIcon.Information,
                        5000
                    )
                reminder['notified'] = True
                self.save_data('reminders.json', self.reminders)
                
    def quit_application(self):
        reply = QMessageBox.question(
            self, 'Quit',
            'Are you sure you want to quit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QApplication.quit()

class PeriodTrackerDialog(QDialog):
    def __init__(self, periods, parent=None):
        super().__init__(parent)
        self.periods = periods
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Period Tracker")
        layout = QVBoxLayout(self)
        
        # Calendars
        calendar_layout = QHBoxLayout()
        
        # Start date calendar
        start_group = QWidget()
        start_layout = QVBoxLayout(start_group)
        start_layout.addWidget(QLabel("Start Date:"))
        self.start_calendar = QCalendarWidget()
        start_layout.addWidget(self.start_calendar)
        calendar_layout.addWidget(start_group)
        
        # End date calendar
        end_group = QWidget()
        end_layout = QVBoxLayout(end_group)
        end_layout.addWidget(QLabel("End Date:"))
        self.end_calendar = QCalendarWidget()
        end_layout.addWidget(self.end_calendar)
        calendar_layout.addWidget(end_group)
        
        layout.addLayout(calendar_layout)
        
        # Add period button
        add_button = QPushButton("Add Period")
        add_button.clicked.connect(self.add_period)
        layout.addWidget(add_button)
        
        # History
        layout.addWidget(QLabel("History:"))
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.update_history()
        layout.addWidget(self.history_text)
        
        # Delete button
        delete_button = QPushButton("Delete Selected Period")
        delete_button.clicked.connect(self.delete_period)
        layout.addWidget(delete_button)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
    def add_period(self):
        start_date = self.start_calendar.selectedDate().toString(Qt.ISODate)
        end_date = self.end_calendar.selectedDate().toString(Qt.ISODate)
        
        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Dates", "Start date must be before end date.")
            return
            
        self.periods.append({
            'start': start_date,
            'end': end_date
        })
        self.update_history()
        
    def delete_period(self):
        selected_text = self.history_text.textCursor().selectedText()
        if not selected_text:
            QMessageBox.warning(self, "No Selection", "Please select a period to delete.")
            return
            
        reply = QMessageBox.question(
            self, 'Delete Period',
            'Are you sure you want to delete this period?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for i, period in enumerate(self.periods):
                period_text = f"From {period['start']} to {period['end']}"
                if period_text in selected_text:
                    del self.periods[i]
                    self.update_history()
                    break
                    
    def update_history(self):
        history = ""
        for period in sorted(self.periods, key=lambda x: x['start'], reverse=True):
            history += f"From {period['start']} to {period['end']}\n"
        self.history_text.setText(history)

class RemindersDialog(QDialog):
    def __init__(self, reminders, parent=None):
        super().__init__(parent)
        self.reminders = reminders
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Reminders")
        layout = QVBoxLayout(self)
        
        # Reminder input
        input_layout = QHBoxLayout()
        self.reminder_input = QLineEdit()
        input_layout.addWidget(QLabel("Reminder:"))
        input_layout.addWidget(self.reminder_input)
        layout.addLayout(input_layout)
        
        # Date and time input
        datetime_layout = QHBoxLayout()
        self.date_input = QCalendarWidget()
        datetime_layout.addWidget(self.date_input)
        
        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.addWidget(QLabel("Time:"))
        self.hour_input = QSpinBox()
        self.hour_input.setRange(0, 23)
        time_layout.addWidget(self.hour_input)
        self.minute_input = QSpinBox()
        self.minute_input.setRange(0, 59)
        time_layout.addWidget(self.minute_input)
        datetime_layout.addWidget(time_widget)
        
        layout.addLayout(datetime_layout)
        
        # Add reminder button
        add_button = QPushButton("Add Reminder")
        add_button.clicked.connect(self.add_reminder)
        layout.addWidget(add_button)
        
        # Reminders list
        layout.addWidget(QLabel("Your Reminders:"))
        self.reminders_list = QTextEdit()
        self.reminders_list.setReadOnly(True)
        self.update_reminders()
        layout.addWidget(self.reminders_list)
        
        # Delete button
        delete_button = QPushButton("Delete Selected Reminder")
        delete_button.clicked.connect(self.delete_reminder)
        layout.addWidget(delete_button)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
    def add_reminder(self):
        reminder_text = self.reminder_input.text().strip()
        if not reminder_text:
            QMessageBox.warning(self, "Invalid Input", "Please enter a reminder text.")
            return
            
        date = self.date_input.selectedDate().toPython()
        time = datetime.now().replace(
            hour=self.hour_input.value(),
            minute=self.minute_input.value(),
            second=0,
            microsecond=0
        ).time()
        reminder_time = datetime.combine(date, time)
        
        if reminder_time < datetime.now():
            QMessageBox.warning(self, "Invalid Time", "Reminder time must be in the future.")
            return
            
        self.reminders.append({
            'text': reminder_text,
            'time': reminder_time.isoformat(),
            'notified': False
        })
        self.reminder_input.clear()
        self.update_reminders()
        
    def delete_reminder(self):
        selected_text = self.reminders_list.textCursor().selectedText()
        if not selected_text:
            QMessageBox.warning(self, "No Selection", "Please select a reminder to delete.")
            return
            
        reply = QMessageBox.question(
            self, 'Delete Reminder',
            'Are you sure you want to delete this reminder?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for i, reminder in enumerate(self.reminders):
                if reminder['text'] in selected_text:
                    del self.reminders[i]
                    self.update_reminders()
                    break
                    
    def update_reminders(self):
        reminders_text = ""
        for reminder in sorted(self.reminders, key=lambda x: x['time']):
            time = datetime.fromisoformat(reminder['time']).strftime('%Y-%m-%d %H:%M')
            status = "✓" if reminder['notified'] else "⏰"
            reminders_text += f"[{time}] {status} {reminder['text']}\n"
        self.reminders_list.setText(reminders_text)

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)
        
        # Pet size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Pet Size:"))
        self.size_input = QSpinBox()
        self.size_input.setRange(50, 300)
        self.size_input.setValue(self.settings['pet_size'])
        size_layout.addWidget(self.size_input)
        layout.addLayout(size_layout)
        
        # Animation speed
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Animation Speed:"))
        self.speed_input = QSpinBox()
        self.speed_input.setRange(50, 200)
        self.speed_input.setValue(self.settings['animation_speed'])
        speed_layout.addWidget(self.speed_input)
        layout.addLayout(speed_layout)
        
        # Stay on top
        self.top_checkbox = QCheckBox("Stay on Top")
        self.top_checkbox.setChecked(self.settings['stay_on_top'])
        layout.addWidget(self.top_checkbox)
        
        # Show notifications
        self.notify_checkbox = QCheckBox("Show Notifications")
        self.notify_checkbox.setChecked(self.settings['show_notifications'])
        layout.addWidget(self.notify_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def save_settings(self):
        self.settings['pet_size'] = self.size_input.value()
        self.settings['animation_speed'] = self.speed_input.value()
        self.settings['stay_on_top'] = self.top_checkbox.isChecked()
        self.settings['show_notifications'] = self.notify_checkbox.isChecked()
        self.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Apply the purple theme
    apply_purple_theme(app)
    
    # Create and show the pet
    pet = DesktopPet()
    pet.show()
    
    sys.exit(app.exec()) 