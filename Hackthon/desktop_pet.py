import sys
import signal
from PySide6.QtWidgets import (QApplication, QLabel, QWidget, QMenu, QSystemTrayIcon,
                              QCalendarWidget, QInputDialog, QMessageBox, QDialog,
                              QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox, QLineEdit,
                              QScrollArea, QFrame, QCheckBox, QTextEdit)
from PySide6.QtCore import Qt, QPoint, QTimer, QDateTime, QTime
from PySide6.QtGui import QMovie, QMouseEvent, QCursor, QAction, QFont
import json
import os
from datetime import datetime, timedelta

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

class NotesDialog(ScrollableDialog):
    def __init__(self, parent=None):
        super().__init__("Notes", parent)
        self.parent_widget = parent
        
        # List frame for notes
        self.list_frame = QFrame()
        self.list_layout = QVBoxLayout(self.list_frame)
        self.content_layout.addWidget(self.list_frame)
        
        # Input frame
        input_frame = QFrame()
        input_layout = QVBoxLayout(input_frame)
        
        self.text_edit = QTextEdit()
        input_layout.addWidget(self.text_edit)
        
        save_button = QPushButton("Save Note")
        save_button.clicked.connect(self.save_note)
        input_layout.addWidget(save_button)
        
        self.content_layout.addWidget(input_frame)
        
        # Load existing notes
        self.load_notes()
    
    def load_notes(self):
        notes = self.parent_widget.data['notes'] if hasattr(self.parent_widget, 'data') else []
        if not notes:
            label = QLabel("No notes")
            label.setStyleSheet("color: gray;")
            self.list_layout.addWidget(label)
        else:
            for note in notes:
                self.add_note_widget(note)
    
    def save_note(self):
        text = self.text_edit.toPlainText().strip()
        if text:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            note = {"timestamp": timestamp, "text": text}
            self.parent_widget.data['notes'].append(note)
            self.parent_widget.save_data()
            self.add_note_widget(note)
            self.text_edit.clear()
    
    def add_note_widget(self, note):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        
        timestamp_label = QLabel(note['timestamp'])
        timestamp_label.setStyleSheet("color: gray;")
        layout.addWidget(timestamp_label)
        
        text_label = QLabel(note['text'])
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        
        delete_btn = QPushButton("Delete")
        layout.addWidget(delete_btn)
        
        self.list_layout.addWidget(frame)

class TimerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle('Timer')
        layout = QVBoxLayout()
        
        # Time input
        time_layout = QHBoxLayout()
        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(1, 60)
        self.minutes_input.setValue(25)
        time_layout.addWidget(QLabel("Minutes:"))
        time_layout.addWidget(self.minutes_input)
        layout.addLayout(time_layout)
        
        # Timer display
        self.time_label = QLabel('00:00')
        layout.addWidget(self.time_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Start button
        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start_timer)
        button_layout.addWidget(self.start_button)
        
        # Close button
        close_button = QPushButton('Close')
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.remaining_seconds = 0

    def closeEvent(self, event):
        """Handle window close event"""
        self.timer.stop()
        self.time_label.setText('00:00')
        self.start_button.setEnabled(True)
        self.remaining_seconds = 0
        event.accept()
        
    def start_timer(self):
        self.remaining_seconds = self.minutes_input.value() * 60
        self.timer.start(1000)
        self.start_button.setEnabled(False)
        
    def update_timer(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            self.time_label.setText(f'{minutes:02d}:{seconds:02d}')
        else:
            self.timer.stop()
            self.start_button.setEnabled(True)
            QMessageBox.information(self, "Timer", "Time's up!")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)  # 使用独立窗口
        self.setWindowTitle('Settings')
        layout = QVBoxLayout()
        
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
        self.setMinimumSize(300, 400)
        
        layout = QVBoxLayout(self)
        
        # Calendar widget
        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar)
        
        # Record button
        record_button = QPushButton("Record This Date")
        record_button.clicked.connect(self.record_date)
        layout.addWidget(record_button)
        
        # History label
        history_label = QLabel("History:")
        layout.addWidget(history_label)
        
        # Scrollable area for history
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        history_widget = QWidget()
        self.history_layout = QVBoxLayout(history_widget)
        scroll.setWidget(history_widget)
        
        # Load history
        self.load_history()
    
    def load_history(self):
        records = self.parent_widget.data['period_records'] if hasattr(self.parent_widget, 'data') else []
        if not records:
            label = QLabel("No records yet")
            label.setStyleSheet("color: gray;")
            self.history_layout.addWidget(label)
        else:
            # Sort records by date, newest first
            records.sort(reverse=True)
            for date in records:
                label = QLabel(date)
                self.history_layout.addWidget(label)
    
    def record_date(self):
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        if selected_date not in self.parent_widget.data['period_records']:
            self.parent_widget.data['period_records'].append(selected_date)
            self.parent_widget.save_data()
            
            # Clear "No records" label if it exists
            while self.history_layout.count():
                item = self.history_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Reload history
            self.load_history()
            
            QMessageBox.information(self, "Success", "Date recorded successfully!")

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        
        # Remove window frame and keep on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # No frame
            Qt.WindowType.WindowStaysOnTopHint | # Always on top
            Qt.WindowType.Tool                   # No taskbar icon
        )
        
        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create label for the pet
        self.pet_label = QLabel(self)
        
        # Initialize states and movies
        self.current_state = 'idle'
        self.movies = self.load_animations()
        self.current_movie = self.movies['idle']
        
        # Set up the pet display
        self.pet_label.setMovie(self.current_movie)
        self.current_movie.start()
        
        # Initialize movement variables
        self.dragging = False
        self.offset = QPoint()
        self.target_pos = None
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.move_to_target)
        self.move_speed = 5
        
        # Initialize data storage
        self.data_file = os.path.join(DATA_DIR, 'pet_data.json')
        self.load_data()
        
        # Store dialog instances
        self.timer_dialog = None
        self.settings_dialog = None
        self.reminder_dialog = None
        self.notes_dialog = None
        self.period_dialog = None
        
        # Set up reminder checker
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # Check every minute
        
        # Set up global mouse tracking
        self.global_timer = QTimer(self)
        self.global_timer.timeout.connect(self.check_global_mouse)
        self.global_timer.start(100)  # Check every 100ms
        
        # Show the widget
        self.show()
        self.adjustSize()
    
    def load_animations(self):
        """Load all animation states"""
        movies = {}
        for state in ['idle', 'happy', 'moving']:
            movie = QMovie(f"{state}.gif")
            if movie.isValid():
                movies[state] = movie
            else:
                # Create an empty movie as fallback
                movies[state] = QMovie()
        return movies
    
    def load_data(self):
        """Load saved data"""
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
        """Save data to file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.position().toPoint()
            self.change_state('happy')
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events"""
        if self.dragging:
            new_pos = self.mapToGlobal(event.position().toPoint() - self.offset)
            self.move(new_pos.x(), new_pos.y())
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.change_state('idle')
    
    def change_state(self, new_state):
        """Change the pet's state and animation"""
        if new_state != self.current_state and new_state in self.movies:
            self.current_state = new_state
            self.pet_label.setMovie(self.movies[new_state])
            self.movies[new_state].start()
    
    def check_global_mouse(self):
        """Check global mouse position and handle following behavior"""
        if self.dragging:
            return
            
        cursor_pos = QCursor.pos()
        
        # Calculate target position (center pet on cursor)
        target_x = cursor_pos.x() - self.width() // 2
        target_y = cursor_pos.y() - self.height() // 2
        
        # Only follow if cursor is far enough
        current_pos = self.pos()
        dx = target_x - current_pos.x()
        dy = target_y - current_pos.y()
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance > 100:  # Only follow if cursor is more than 100 pixels away
            self.target_pos = QPoint(target_x, target_y)
            if self.current_state != 'moving':
                self.change_state('moving')
            
            if not self.move_timer.isActive():
                self.move_timer.start(50)
    
    def move_to_target(self):
        """Move pet towards target position"""
        if not self.target_pos:
            return
        
        current_pos = self.pos()
        dx = self.target_pos.x() - current_pos.x()
        dy = self.target_pos.y() - current_pos.y()
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance <= self.move_speed:
            # Reached target
            self.move(self.target_pos.x(), self.target_pos.y())
            self.target_pos = None
            self.move_timer.stop()
            self.change_state('idle')
        else:
            # Move towards target
            ratio = self.move_speed / distance
            new_x = current_pos.x() + int(dx * ratio)
            new_y = current_pos.y() + int(dy * ratio)
            self.move(new_x, new_y)
    
    def closeEvent(self, event):
        """Clean up when closing"""
        self.global_timer.stop()
        self.move_timer.stop()
        self.reminder_timer.stop()
        self.save_data()
        super().closeEvent(event)

    def cleanup(self):
        """Clean up resources and save data"""
        if self.timer_dialog:
            self.timer_dialog.timer.stop()  # Make sure to stop the timer
            self.timer_dialog.close()
        if self.settings_dialog:
            self.settings_dialog.close()
        if self.reminder_dialog:
            self.reminder_dialog.close()
        if self.notes_dialog:
            self.notes_dialog.close()
        if self.period_dialog:
            self.period_dialog.close()
        self.global_timer.stop()
        self.move_timer.stop()
        self.reminder_timer.stop()
        self.save_data()
        QApplication.quit()

    def contextMenuEvent(self, event):
        """Handle right-click menu"""
        menu = QMenu(self)
        
        # Notes submenu
        notes_menu = menu.addMenu("Notes")
        notes_menu.addAction("Add Note", self.show_notes)
        notes_menu.addAction("View Notes", self.show_notes)
        
        # Period tracking submenu
        period_menu = menu.addMenu("Period Tracking")
        period_menu.addAction("Manage Period Records", self.show_period_dialog)
        
        # Reminders submenu
        reminders_menu = menu.addMenu("Reminders")
        reminders_menu.addAction("Manage Reminders", self.show_reminders)
        
        # Timer
        menu.addAction("Timer", self.show_timer)
        
        # Settings
        menu.addAction("Settings", self.show_settings)
        
        # Exit option
        menu.addSeparator()
        menu.addAction("Exit", self.cleanup)
        
        menu.exec(event.globalPos())

    def show_reminders(self):
        if not self.reminder_dialog:
            self.reminder_dialog = ReminderDialog(self)
        self.reminder_dialog.show()
        self.reminder_dialog.raise_()

    def show_notes(self):
        if not self.notes_dialog:
            self.notes_dialog = NotesDialog(self)
        self.notes_dialog.show()
        self.notes_dialog.raise_()

    def show_period_dialog(self):
        """Show period tracking dialog"""
        if not self.period_dialog:
            self.period_dialog = PeriodDialog(self)
        self.period_dialog.show()
        self.period_dialog.raise_()

    def show_timer(self):
        """Show timer dialog"""
        if not self.timer_dialog:
            self.timer_dialog = TimerDialog(None)  # Create as independent window
        self.timer_dialog.show()
        self.timer_dialog.raise_()

    def show_settings(self):
        """Show settings dialog"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        if self.settings_dialog.exec() == QDialog.DialogCode.Accepted:
            self.move_speed = self.settings_dialog.speed_input.value()

    def check_reminders(self):
        """Check for due reminders"""
        current_time = datetime.now()
        reminders_to_remove = []
        
        for reminder in self.data['reminders']:
            if 'datetime' not in reminder:
                continue
                
            try:
                reminder_time = datetime.strptime(reminder['datetime'], "%Y-%m-%d %H:%M:%S")
                if reminder_time <= current_time:
                    QMessageBox.information(None, "Reminder!", reminder['text'])
                    reminders_to_remove.append(reminder)
            except (ValueError, TypeError):
                continue
        
        # Remove triggered reminders
        for reminder in reminders_to_remove:
            self.data['reminders'].remove(reminder)
        
        if reminders_to_remove:
            self.save_data()

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    if 'pet' in globals():
        pet.cleanup()
    sys.exit(0)

if __name__ == '__main__':
    # Suppress Qt warnings
    if not sys.warnoptions:
        import warnings
        warnings.filterwarnings('ignore', category=RuntimeWarning, module='PySide6.QtGui')
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    app = QApplication(sys.argv)
    
    # Suppress native menu bar on macOS
    if sys.platform == 'darwin':
        app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar)
    
    pet = DesktopPet()
    
    # Allow clean shutdown on Ctrl+C
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Let Python process signals
    timer.start(200)
    
    sys.exit(app.exec()) 