import sys
import signal
import json
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import traceback

from PySide6.QtWidgets import (QApplication, QLabel, QWidget, QMenu, QSystemTrayIcon,
                              QCalendarWidget, QInputDialog, QMessageBox, QDialog,
                              QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox, QLineEdit,
                              QScrollArea, QFrame, QCheckBox, QTextEdit)
from PySide6.QtCore import Qt, QPoint, QTimer, QDateTime, QTime, QSize, QUrl
from PySide6.QtGui import QMovie, QMouseEvent, QCursor, QAction, QFont, QPalette, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

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
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

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

class TodoListDialog(ScrollableDialog):
    def __init__(self, parent=None):
        logging.info("TodoListDialog: __init__ called")
        try:
            super().__init__("Todo List", parent)
            self.parent_widget = parent
            # List frame for todos
            self.list_frame = QFrame()
            self.list_layout = QVBoxLayout(self.list_frame)
            self.content_layout.addWidget(self.list_frame)
            # Input frame for new todo
            input_frame = QFrame()
            input_layout = QHBoxLayout(input_frame)
            # Text input
            self.text_input = QLineEdit()
            self.text_input.setPlaceholderText("Add new todo...")
            self.text_input.returnPressed.connect(self.add_todo)  # Add todo when Enter is pressed
            input_layout.addWidget(self.text_input)
            # Add button
            add_button = QPushButton("Add")
            add_button.clicked.connect(self.add_todo)
            input_layout.addWidget(add_button)
            self.content_layout.addWidget(input_frame)
            # Load existing todos
            self.load_todos()
        except Exception as e:
            logging.error(f"Exception in TodoListDialog.__init__: {e}\n{traceback.format_exc()}")
            raise
        logging.info("TodoListDialog: __init__ finished")

    def load_todos(self):
        todos = self.parent_widget.data.get('todos', []) if hasattr(self.parent_widget, 'data') else []
        if not todos:
            label = QLabel("No todos yet")
            label.setStyleSheet("color: gray;")
            self.list_layout.addWidget(label)
        else:
            for todo in todos:
                self.add_todo_widget(todo)

    def add_todo_widget(self, todo):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setChecked(todo.get('completed', False))
        checkbox.stateChanged.connect(lambda state, t=todo: self.toggle_todo(t, state))
        layout.addWidget(checkbox)
        # Todo text
        label = QLabel(todo['text'])
        label.setWordWrap(True)
        if todo.get('completed', False):
            label.setStyleSheet("text-decoration: line-through; color: gray;")
        layout.addWidget(label)
        # Delete button
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(30, 30)  # Set fixed size for delete button
        delete_btn.setStyleSheet("""
            QPushButton {
                color: #FF4444;
                border: none;
                font-size: 16px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #FFE0E0;
                border-radius: 3px;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_todo(todo, frame))
        layout.addWidget(delete_btn)
        self.list_layout.addWidget(frame)

    def add_todo(self):
        text = self.text_input.text().strip()
        if text:
            todo = {
                'text': text,
                'completed': False
            }
            # Initialize todos list if it doesn't exist
            if not hasattr(self.parent_widget, 'data'):
                self.parent_widget.data = {}
            if 'todos' not in self.parent_widget.data:
                self.parent_widget.data['todos'] = []
            self.parent_widget.data['todos'].append(todo)
            self.parent_widget.save_data()
            # Clear input
            self.text_input.clear()
            # Clear existing todos and reload
            while self.list_layout.count():
                item = self.list_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.load_todos()

    def toggle_todo(self, todo, state):
        todo['completed'] = (state == Qt.CheckState.Checked.value)
        self.parent_widget.save_data()
        # Update the label style
        frame = self.sender().parent()
        label = frame.findChild(QLabel)
        if label:
            if todo['completed']:
                label.setStyleSheet("text-decoration: line-through; color: gray;")
            else:
                label.setStyleSheet("")

    def delete_todo(self, todo, frame):
        if todo in self.parent_widget.data['todos']:
            self.parent_widget.data['todos'].remove(todo)
            self.parent_widget.save_data()
            frame.deleteLater()
            # Show "No todos" if list is empty
            if not self.parent_widget.data['todos']:
                label = QLabel("No todos yet")
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
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            
            # Clear existing notes and reload
            while self.list_layout.count():
                item = self.list_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            self.load_notes()
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
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        
        # Size setting
        size_layout = QHBoxLayout()
        self.size_slider = QSpinBox()
        self.size_slider.setRange(50, 200)  # Size range from 50% to 200%
        self.size_slider.setValue(parent.pet_size if parent else 100)
        self.size_slider.setSuffix("%")
        size_layout.addWidget(QLabel("Pet Size:"))
        size_layout.addWidget(self.size_slider)
        layout.addLayout(size_layout)
        
        # Volume setting
        volume_layout = QHBoxLayout()
        self.volume_slider = QSpinBox()
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(parent.audio_output.volume() * 100) if parent else 100)
        self.volume_slider.setSuffix("%")
        volume_layout.addWidget(QLabel("Sound Volume:"))
        volume_layout.addWidget(self.volume_slider)
        layout.addLayout(volume_layout)
        
        # OK button
        ok_button = QPushButton('Apply')
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        
        self.setLayout(layout)

    def accept(self):
        if self.parent():
            self.parent().move_speed = self.speed_input.value()
            self.parent().follow_mouse = self.follow_checkbox.isChecked()
            new_size = self.size_slider.value()
            if new_size != self.parent().pet_size:
                self.parent().pet_size = new_size
                self.parent().update_pet_size()
                self.parent().data['pet_size'] = self.parent().pet_size
                self.parent().save_data()
            # Apply volume setting
            self.parent().audio_output.setVolume(self.volume_slider.value() / 100.0)
        super().accept()

class PeriodDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.parent_widget = parent
        self.setWindowTitle("Period Tracking")
        self.setMinimumSize(400, 500)  # Reduced overall size
        
        # Initialize date selection variables
        self.start_date = None
        self.end_date = None
        self.is_selecting_start = True
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Instructions label
        instructions = QLabel("Click on calendar to select start date, then end date")
        instructions.setStyleSheet("color: #6A5ACD; font-weight: bold;")
        layout.addWidget(instructions)
        
        # Calendar with styling
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumSize(300, 300)  # Reduced calendar size
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)  # Hide week numbers
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
                font-size: 14px;  /* Reduced font size */
                font-weight: bold;
                padding: 3px;  /* Reduced padding */
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
                padding: 2px;  /* Reduced padding */
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: #E6E6FA;
                color: #323250;
                selection-background-color: #6A5ACD;
                selection-color: white;
                font-size: 12px;  /* Reduced font size */
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #A0A0A0;
            }
            /* Highlight weekends */
            QCalendarWidget QAbstractItemView:enabled[dayOfWeek="6"],
            QCalendarWidget QAbstractItemView:enabled[dayOfWeek="7"] {
                color: #6A5ACD;
                font-weight: bold;
            }
        """)
        self.calendar.clicked.connect(self.handle_date_selection)
        layout.addWidget(self.calendar)
        
        # Record button with styling
        record_button = QPushButton("Record Period")
        record_button.setStyleSheet("""
            QPushButton {
                background-color: #6A5ACD;
                color: white;
                font-size: 14px;
                padding: 8px;  /* Reduced padding */
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5A4ABD;
            }
            QPushButton:disabled {
                background-color: #C8C8E6;
                color: #A0A0A0;
            }
        """)
        record_button.clicked.connect(self.record_period)
        record_button.setEnabled(False)  # Disable until both dates are selected
        self.record_button = record_button
        layout.addWidget(record_button)
        
        # Selected date range display - moved to bottom
        self.range_label = QLabel("Selected Range: None")
        self.range_label.setStyleSheet("color: #6A5ACD; font-weight: bold; font-size: 14px;")
        self.range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.range_label)
        
        # History section
        history_label = QLabel("History:")
        history_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(history_label)
        
        # Scrollable area for history
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #C8C8E6;
                border-radius: 5px;
            }
        """)
        layout.addWidget(scroll)
        
        history_widget = QWidget()
        self.history_layout = QVBoxLayout(history_widget)
        self.history_layout.setSpacing(10)
        scroll.setWidget(history_widget)
        
        # Load history
        self.load_history()
    
    def handle_date_selection(self, date):
        if self.is_selecting_start:
            self.start_date = date
            self.is_selecting_start = False
            self.range_label.setText(f"Selected Range: {date.toString('yyyy-MM-dd')} to ...")
            self.highlight_date_range()
        else:
            self.end_date = date
            if self.end_date < self.start_date:
                # Swap dates if end date is before start date
                self.start_date, self.end_date = self.end_date, self.start_date
            
            self.range_label.setText(f"Selected Range: {self.start_date.toString('yyyy-MM-dd')} to {self.end_date.toString('yyyy-MM-dd')}")
            self.record_button.setEnabled(True)
            self.is_selecting_start = True
            self.highlight_date_range()
    
    def highlight_date_range(self):
        if not self.start_date:
            return
            
        # Reset calendar style
        base_style = self.calendar.styleSheet()
        self.calendar.setStyleSheet(base_style)
        
        # Add highlighting for the range
        if self.end_date:
            current_date = self.start_date
            while current_date <= self.end_date:
                date_str = current_date.toString("yyyy-MM-dd")
                style = self.calendar.styleSheet()
                style += f"""
                    QCalendarWidget QAbstractItemView:enabled[date="{date_str}"] {{
                        background-color: #6A5ACD;
                        color: white;
                    }}
                """
                self.calendar.setStyleSheet(style)
                current_date = current_date.addDays(1)
        else:
            # Highlight only start date
            date_str = self.start_date.toString("yyyy-MM-dd")
            style = self.calendar.styleSheet()
            style += f"""
                QCalendarWidget QAbstractItemView:enabled[date="{date_str}"] {{
                    background-color: #6A5ACD;
                    color: white;
                }}
            """
            self.calendar.setStyleSheet(style)
    
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
        if not self.start_date or not self.end_date:
            return
        
        # Create new record
        new_record = {
            'start_date': self.start_date.toString("yyyy-MM-dd"),
            'end_date': self.end_date.toString("yyyy-MM-dd")
        }
        
        # Initialize period_records if it doesn't exist
        if 'period_records' not in self.parent_widget.data:
            self.parent_widget.data['period_records'] = []
        
        # Add the new record
        self.parent_widget.data['period_records'].append(new_record)
        self.parent_widget.save_data()
        
        # Reset selection
        self.start_date = None
        self.end_date = None
        self.is_selecting_start = True
        self.range_label.setText("Selected Range: None")
        self.record_button.setEnabled(False)
        
        # Reset calendar highlighting
        self.calendar.setStyleSheet(self.calendar.styleSheet())
        
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
        
        # Set object name for styling BEFORE applying any styles
        self.setObjectName("DesktopPet")
        
        # Remove window frame, keep on top, and remove shadow
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # No frame
            Qt.WindowType.WindowStaysOnTopHint | # Always on top
            Qt.WindowType.Tool |                # No taskbar icon
            Qt.WindowType.NoDropShadowWindowHint # Remove shadow
        )
        
        # Enable transparency and disable window shadow
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
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
        self.pet_size = 100  # Default size is 100%
        
        # Initialize data storage
        self.data_file = os.path.join(DATA_DIR, 'pet_data.json')
        self.load_data()
        
        # Store dialog instances
        self.settings_dialog = None
        self.todo_dialog = None
        self.notes_dialog = None
        self.period_dialog = None
        
        # Set up global mouse tracking
        self.global_timer = QTimer(self)
        self.global_timer.timeout.connect(self.check_global_mouse)
        self.global_timer.start(100)  # Check every 100ms
        
        # Initialize media player for sound effects
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)  # Set volume to 100%
        
        # Load the sound file with absolute path and error handling
        sound_path = resource_path("Hackthon/oiia-oiia-sound.mp3")
        logging.info(f"Loading sound file from: {sound_path}")
        
        if not os.path.exists(sound_path):
            logging.error(f"Sound file not found at: {sound_path}")
        else:
            logging.info("Sound file exists, attempting to load...")
            self.media_player.setSource(QUrl.fromLocalFile(sound_path))
            # Stop any auto-play
            self.media_player.stop()
            
        # Connect error handler and media status handler for looping
        self.media_player.errorOccurred.connect(self.handle_media_error)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        
        # Apply additional styling specific to the pet window
        self.setStyleSheet("""
            QWidget#DesktopPet {
                background-color: transparent;
            }
            QLabel {
                background-color: transparent;
            }
        """)
        
        # Show the widget
        self.show()
        self.adjustSize()
        self.raise_()
        self.activateWindow()
        
        # Apply initial size
        self.update_pet_size()
    
    def update_pet_size(self):
        """Update the pet's size based on the size setting"""
        if not self.current_movie:
            return
            
        # Get the original size of the current frame
        original_size = self.current_movie.currentPixmap().size()
        
        # Calculate new size based on percentage
        new_width = int(original_size.width() * self.pet_size / 100)
        new_height = int(original_size.height() * self.pet_size / 100)
        
        # Set the new size for all movies
        for movie in self.movies.values():
            movie.setScaledSize(QSize(new_width, new_height))
        
        # Set the new size for the label
        self.pet_label.setFixedSize(new_width, new_height)
        self.adjustSize()

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
                # Load saved size
                self.pet_size = self.data.get('pet_size', 100)
        else:
            self.data = {
                'notes': [],
                'period_records': [],
                'todos': [],
                'pet_size': 100
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
            old_state = self.current_state
            self.current_state = new_state
            self.pet_label.setMovie(self.movies[new_state])
            self.movies[new_state].start()
            
            # Stop sound if we're changing from moving to any other state
            if old_state == 'moving' and new_state != 'moving':
                self.media_player.stop()
    
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
            # Only start playing sound if we're transitioning to moving state
            if self.current_state != 'moving':
                self.change_state('moving')
                # Start playing sound when movement begins
                self.media_player.setPosition(0)  # Reset to start of sound
                self.media_player.play()
            
            if not self.move_timer.isActive():
                self.move_timer.start(50)
        else:
            # If we're not moving anymore, change state back to idle
            if self.current_state == 'moving':
                self.change_state('idle')
                # Stop sound when movement stops
                self.media_player.stop()
    
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
        self.save_data()
        super().closeEvent(event)

    def cleanup(self):
        """Clean up resources and save data"""
        if hasattr(self, 'settings_dialog') and self.settings_dialog:
            self.settings_dialog.close()
        if hasattr(self, 'todo_dialog') and self.todo_dialog:
            self.todo_dialog.close()
        if hasattr(self, 'notes_dialog') and self.notes_dialog:
            self.notes_dialog.close()
        if hasattr(self, 'period_dialog') and self.period_dialog:
            self.period_dialog.close()
        
        # Stop and release media player
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        self.global_timer.stop()
        self.move_timer.stop()
        self.save_data()
        QApplication.quit()

    def contextMenuEvent(self, event):
        """Handle right-click menu"""
        menu = QMenu(self)
        
        # Notes
        menu.addAction("Notes", self.show_notes)
        
        # Period tracking
        menu.addAction("Period Tracking", self.show_period_dialog)
        
        # Todo List
        menu.addAction("Todo List", self.show_todo_list)
        
        # Settings
        menu.addAction("Settings", self.show_settings)
        
        # Exit option
        menu.addSeparator()
        menu.addAction("Exit", self.cleanup)
        
        menu.exec(event.globalPos())

    def show_todo_list(self):
        """Show todo list dialog"""
        logging.info("show_todo_list called")
        try:
            dialog = TodoListDialog(self)
            dialog.exec()  # Show modally for testing
        except Exception as e:
            logging.error(f"Exception in show_todo_list: {e}\n{traceback.format_exc()}")

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
            new_size = self.settings_dialog.size_slider.value()
            if new_size != self.pet_size:
                self.pet_size = new_size
                self.update_pet_size()
                # Save size to data
                self.data['pet_size'] = self.pet_size
                self.save_data()

    def handle_media_status(self, status):
        """Handle media status changes for looping"""
        # When the media reaches the end, if we're still in moving state, loop it
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.current_state == 'moving':
            self.media_player.setPosition(0)  # Reset to start
            self.media_player.play()  # Play again

    def handle_media_error(self, error, error_string):
        """Handle media player errors"""
        logging.error(f"Media player error {error}: {error_string}")

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
    
    # Apply the light purple theme BEFORE creating any widgets
    apply_light_purple_theme()
    
    # Suppress native menu bar on macOS
    if sys.platform == 'darwin':
        app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar)
    
    # Create the pet after theme is applied
    pet = DesktopPet()
    
    # Allow clean shutdown on Ctrl+C
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Let Python process signals
    timer.start(200)
    
    sys.exit(app.exec()) 