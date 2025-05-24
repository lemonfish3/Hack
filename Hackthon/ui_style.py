from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

def apply_purple_theme(app):
    """Apply a light purple theme to the application"""
    palette = QPalette()
    
    # Set color scheme
    primary_color = QColor(147, 112, 219)     # Light purple
    secondary_color = QColor(230, 230, 250)    # Lavender
    text_color = QColor(48, 25, 52)           # Dark purple
    
    # Window colors
    palette.setColor(QPalette.Window, secondary_color)
    palette.setColor(QPalette.WindowText, text_color)
    
    # Button colors
    palette.setColor(QPalette.Button, primary_color)
    palette.setColor(QPalette.ButtonText, Qt.white)
    
    # Input field colors
    palette.setColor(QPalette.Base, Qt.white)
    palette.setColor(QPalette.Text, text_color)
    
    # Highlight colors
    palette.setColor(QPalette.Highlight, primary_color)
    palette.setColor(QPalette.HighlightedText, Qt.white)
    
    # Disabled colors
    palette.setColor(QPalette.Disabled, QPalette.Window, QColor(200, 200, 200))
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(120, 120, 120))
    palette.setColor(QPalette.Disabled, QPalette.Base, QColor(200, 200, 200))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(120, 120, 120))
    
    app.setPalette(palette)
    
    # Set stylesheet for custom styling
    app.setStyleSheet("""
        QMainWindow {
            background: transparent;
        }
        
        QDialog {
            background-color: #E6E6FA;
        }
        
        QPushButton {
            background-color: #9370DB;
            color: white;
            border: none;
            padding: 5px 15px;
            border-radius: 3px;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #8A5FD7;
        }
        
        QPushButton:pressed {
            background-color: #7B52C3;
        }
        
        QLineEdit, QTextEdit {
            background-color: white;
            border: 1px solid #9370DB;
            border-radius: 3px;
            padding: 3px;
        }
        
        QCalendarWidget {
            background-color: white;
            border: 1px solid #9370DB;
        }
        
        QCalendarWidget QToolButton {
            color: #301934;
        }
        
        QCalendarWidget QMenu {
            background-color: white;
        }
        
        QCalendarWidget QSpinBox {
            background-color: white;
            border: 1px solid #9370DB;
            border-radius: 3px;
        }
        
        QSpinBox {
            background-color: white;
            border: 1px solid #9370DB;
            border-radius: 3px;
            padding: 3px;
        }
        
        QCheckBox {
            color: #301934;
        }
        
        QCheckBox::indicator {
            width: 15px;
            height: 15px;
        }
        
        QCheckBox::indicator:unchecked {
            border: 1px solid #9370DB;
            background-color: white;
        }
        
        QCheckBox::indicator:checked {
            border: 1px solid #9370DB;
            background-color: #9370DB;
        }
        
        QLabel {
            color: #301934;
        }
        
        QMenu {
            background-color: white;
            border: 1px solid #9370DB;
        }
        
        QMenu::item {
            padding: 5px 20px;
        }
        
        QMenu::item:selected {
            background-color: #9370DB;
            color: white;
        }
    """) 