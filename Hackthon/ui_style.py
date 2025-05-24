from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

def apply_light_purple_theme():
    """Apply a light purple theme to the entire application"""
    app = QApplication.instance()
    if app is None:
        return

    # Create a new palette
    palette = QPalette()

    # Define colors
    light_purple = QColor(230, 230, 250)  # Very light purple
    medium_purple = QColor(200, 200, 230)  # Medium light purple
    dark_purple = QColor(150, 150, 200)    # Darker purple for contrast
    text_color = QColor(50, 50, 80)        # Dark purple for text

    # Set colors for different roles
    palette.setColor(QPalette.Window, light_purple)
    palette.setColor(QPalette.WindowText, text_color)
    palette.setColor(QPalette.Base, light_purple)
    palette.setColor(QPalette.AlternateBase, medium_purple)
    palette.setColor(QPalette.ToolTipBase, light_purple)
    palette.setColor(QPalette.ToolTipText, text_color)
    palette.setColor(QPalette.Text, text_color)
    palette.setColor(QPalette.Button, medium_purple)
    palette.setColor(QPalette.ButtonText, text_color)
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.Link, dark_purple)
    palette.setColor(QPalette.Highlight, dark_purple)
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    # Apply the palette
    app.setPalette(palette)

    # Set stylesheet for additional styling
    app.setStyleSheet("""
        /* Make main pet window transparent */
        QWidget#DesktopPet {
            background-color: transparent;
        }
        
        /* Style for all other windows */
        QDialog {
            background-color: #E6E6FA;
        }
        QMenu {
            background-color: #E6E6FA;
            border: 1px solid #C8C8E6;
        }
        QMenu::item {
            padding: 5px 20px;
        }
        QMenu::item:selected {
            background-color: #C8C8E6;
        }
        
        /* Button styling with progressive darkening */
        QPushButton {
            background-color: #D8D8F0;  /* Light purple base */
            border: 1px solid #B4B4E6;
            border-radius: 4px;
            padding: 5px 15px;
            color: #323250;
        }
        QPushButton:hover {
            background-color: #C8C8E6;  /* Slightly darker on hover */
            border: 1px solid #A4A4D6;
        }
        QPushButton:pressed {
            background-color: #B4B4E6;  /* Even darker when pressed */
            border: 1px solid #9494C6;
        }
        
        QLineEdit, QTextEdit, QSpinBox {
            background-color: #FFFFFF;
            border: 1px solid #C8C8E6;
            border-radius: 4px;
            padding: 3px;
        }
        QScrollArea {
            border: 1px solid #C8C8E6;
            background-color: #E6E6FA;
        }
        QFrame {
            background-color: #E6E6FA;
        }
        QLabel {
            color: #323250;
        }
        QCalendarWidget {
            background-color: #E6E6FA;
        }
        QCalendarWidget QToolButton {
            color: #323250;
            background-color: #D8D8F0;  /* Match button base color */
            border: 1px solid #B4B4E6;
            border-radius: 4px;
        }
        QCalendarWidget QToolButton:hover {
            background-color: #C8C8E6;  /* Match button hover color */
            border: 1px solid #A4A4D6;
        }
        QCalendarWidget QToolButton:pressed {
            background-color: #B4B4E6;  /* Match button pressed color */
            border: 1px solid #9494C6;
        }
        QCalendarWidget QMenu {
            background-color: #E6E6FA;
        }
        QCalendarWidget QSpinBox {
            background-color: #FFFFFF;
            border: 1px solid #C8C8E6;
        }
    """) 