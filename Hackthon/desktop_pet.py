import sys
import signal
import json
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QLabel, QWidget, QMenu, QSystemTrayIcon,
                              QCalendarWidget, QInputDialog, QMessageBox, QDialog,
                              QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox, QLineEdit,
                              QScrollArea, QFrame, QCheckBox, QTextEdit)
from PySide6.QtCore import Qt, QPoint, QTimer, QDateTime, QTime, QSize
from PySide6.QtGui import QMovie, QMouseEvent, QCursor, QAction, QFont, QPalette, QColor

from ui_style import apply_light_purple_theme  # Import the UI styling

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.expanduser('~'), '.desktop_pet', 'app.log')),
        logging.StreamHandler()
    ]
)

# 确保数据目录存在
DATA_DIR = os.path.join(os.path.expanduser('~'), '.desktop_pet')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

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
        delete_btn.clicked.connect(lambda: self.delete_note(note, frame))
        layout.addWidget(delete_btn)
        
        self.list_layout.addWidget(frame)

    def delete_note(self, note, frame):
        if note in self.parent_widget.data['notes']:
            self.parent_widget.data['notes'].remove(note)
            self.parent_widget.save_data()
            frame.deleteLater()
            
            # Show "No notes" if list is empty
            if not self.parent_widget.data['notes']:
                label = QLabel("No notes")
                label.setStyleSheet("color: gray;")
                self.list_layout.addWidget(label)

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
        self.setMinimumSize(500, 600)  # Adjusted size for single calendar
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Date selection frame
        date_frame = QFrame()
        date_layout = QVBoxLayout(date_frame)
        
        # Calendar with styling
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumSize(400, 400)
        self.calendar.setStyleSheet("""
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
        date_layout.addWidget(self.calendar)
        
        # Record button with styling
        record_button = QPushButton("Record Period")
        record_button.setStyleSheet("""
            QPushButton {
                background-color: #6A5ACD;
                color: white;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5A4ABD;
            }
        """)
        record_button.clicked.connect(self.record_period)
        date_layout.addWidget(record_button)
        
        layout.addWidget(date_frame)
        
        # History section
        history_frame = QFrame()
        history_layout = QVBoxLayout(history_frame)
        
        history_label = QLabel("History:")
        history_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        history_layout.addWidget(history_label)
        
        # Scrollable area for history
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #C8C8E6;
                border-radius: 5px;
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
            label.setStyleSheet("color: gray;")
            self.history_layout.addWidget(label)
        else:
            # Sort records by start date
            records.sort(key=lambda x: x['start_date'], reverse=True)
            for record in records:
                # Create a frame for each record
                record_frame = QFrame()
                record_layout = QHBoxLayout(record_frame)
                
                # Date label
                label = QLabel(f"From {record['start_date']} to {record['end_date']}")
                record_layout.addWidget(label)
                
                # Delete button
                delete_btn = QPushButton("Delete")
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
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        
        # Create new record
        new_record = {
            'start_date': selected_date,
            'end_date': selected_date
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

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        
        # Set object name for styling
        self.setObjectName("DesktopPet")
        
        # Remove window frame and keep on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # No frame
            Qt.WindowType.WindowStaysOnTopHint | # Always on top
            Qt.WindowType.Tool                   # No taskbar icon
        )
        
        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Explicitly set transparent palette for the main window
        transparent_palette = QPalette()
        transparent_palette.setColor(QPalette.Window, QColor(0, 0, 0, 0))
        self.setPalette(transparent_palette)
        
        # Create label for the pet
        self.pet_label = QLabel(self)
        self.pet_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.pet_label.setStyleSheet("background: transparent;")
        
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
        self.follow_mouse = True  # Add mouse following state
        
        # Initialize data storage
        self.data_file = os.path.join(DATA_DIR, 'pet_data.json')
        self.load_data()
        
        # Store dialog instances
        # self.timer_dialog = None  # Commented out timer dialog
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
        self.raise_()
        self.activateWindow()
    
    def load_animations(self):
        """Load all animation states"""
        movies = {}
        for state in ['idle', 'happy', 'moving']:
            movie = QMovie(resource_path(f"Hackthon/{state}.gif"))
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
        if self.dragging or not self.follow_mouse:  # Check if following is enabled
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
        # if self.timer_dialog:  # Commented out timer cleanup
        #     self.timer_dialog.timer.stop()  # Make sure to stop the timer
        #     self.timer_dialog.close()
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
        # menu.addAction("Timer", self.show_timer)  # Commented out timer menu item
        
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

    def show_settings(self):
        """Show settings dialog"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        if self.settings_dialog.exec() == QDialog.DialogCode.Accepted:
            self.move_speed = self.settings_dialog.speed_input.value()
            self.follow_mouse = self.settings_dialog.follow_checkbox.isChecked()

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
    print("DesktopPet is starting...")
    # Suppress Qt warnings
    if not sys.warnoptions:
        import warnings
        warnings.filterwarnings('ignore', category=RuntimeWarning, module='PySide6.QtGui')
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    app = QApplication(sys.argv)
    
    # Apply the light purple theme
    apply_light_purple_theme()
    
    # Suppress native menu bar on macOS
    if sys.platform == 'darwin':
        app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar)
    
    pet = DesktopPet()
    
    # Allow clean shutdown on Ctrl+C
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Let Python process signals
    timer.start(200)
    
    sys.exit(app.exec()) 