import sys
import os
import json
from typing import List, Dict
import threading

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QSplitter, QScrollArea, QFrame,
    QAction, QMenu
)
from PyQt5.QtCore import Qt, pyqtSignal as Signal, QObject, pyqtSlot as Slot
from PyQt5.QtGui import QFont, QColor, QPalette, QFontDatabase, QIcon

import anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Signal class for thread communication
class WorkerSignals(QObject):
    finished = Signal(str)
    error = Signal(str)

class AnthropicWorker(threading.Thread):
    def __init__(self, prompt: str, message_history: List[Dict], signals: WorkerSignals):
        super().__init__()
        self.prompt = prompt
        self.message_history = message_history
        self.signals = signals
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
    def run(self):
        try:
            # Convert message history to the format expected by Anthropic
            messages = []
            for msg in self.message_history:
                messages.append(msg)
            
            # Add the current prompt
            messages.append({"role": "user", "content": self.prompt})
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=messages
            )
            
            # Get the response text
            response_text = response.content[0].text
            
            # Emit the signal with the response
            self.signals.finished.emit(response_text)
        except Exception as e:
            self.signals.error.emit(str(e))

class MessageWidget(QWidget):
    def __init__(self, message: str, is_user: bool = False, is_dark_theme: bool = False, parent=None):
        super().__init__(parent)
        self.message = message
        self.is_user = is_user
        self.is_dark_theme = is_dark_theme
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create role label with softer styling
        role_label = QLabel("You:" if self.is_user else "Claude:")
        role_font = QFont()
        role_font.setBold(True)
        role_font.setPointSize(11)  # Increased font size
        role_label.setFont(role_font)
        
        if self.is_dark_theme:
            role_label.setStyleSheet("color: #cccccc; margin-left: 5px;")
        else:
            role_label.setStyleSheet("color: #555555; margin-left: 5px;")
        
        # Create message text box with softer styling
        message_box = QTextEdit()
        message_box.setReadOnly(True)
        message_box.setText(self.message)
        message_box.setFrameShape(QTextEdit.NoFrame)
        
        # Set font size for message box
        message_font = QFont()
        message_font.setPointSize(11)  # Increased font size
        message_box.setFont(message_font)
        
        # Set different background colors for user and assistant based on theme
        if self.is_dark_theme:
            if self.is_user:
                message_box.setStyleSheet("""
                    background-color: #3a3f44; 
                    border-radius: 12px; 
                    padding: 15px;
                    color: #e0e0e0;
                    border: 1px solid #4a4f54;
                """)
            else:
                message_box.setStyleSheet("""
                    background-color: #2d5986; 
                    border-radius: 12px; 
                    padding: 15px;
                    color: #ffffff;
                    border: 1px solid #3269a0;
                """)
        else:
            if self.is_user:
                message_box.setStyleSheet("""
                    background-color: #eeeeee; 
                    border-radius: 12px; 
                    padding: 15px;
                    color: #333333;
                    border: 1px solid #dddddd;
                """)
            else:
                message_box.setStyleSheet("""
                    background-color: #d9eaf7; 
                    border-radius: 12px; 
                    padding: 15px;
                    color: #333333;
                    border: 1px solid #bbd6ef;
                """)
        
        layout.addWidget(role_label)
        layout.addWidget(message_box)
        layout.setSpacing(5)
        self.setLayout(layout)

class ChatBotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.message_history = []
        self.is_dark_theme = True  # Default to dark theme
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Claude Chat Bot")
        self.setGeometry(100, 100, 900, 700)
        
        # Main widget and layout
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Chat history area with softer styling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(15, 15, 15, 15)
        self.chat_layout.setSpacing(15)
        self.chat_layout.addStretch()
        
        self.scroll_area.setWidget(self.chat_widget)
        
        # Input area with softer styling
        self.input_widget = QWidget()
        self.input_layout = QVBoxLayout()
        self.input_layout.setContentsMargins(15, 15, 15, 15)
        self.input_layout.setSpacing(10)
        
        # Prompt label
        self.prompt_label = QLabel("Your message:")
        
        # Prompt text box
        self.prompt_text = QTextEdit()
        self.prompt_text.setMinimumHeight(100)
        self.prompt_text.setMaximumHeight(150)
        self.prompt_text.setPlaceholderText("Type your message here...")
        
        # Set font size for prompt text
        prompt_font = QFont()
        prompt_font.setPointSize(11)  # Increased font size
        self.prompt_text.setFont(prompt_font)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setIcon(self.style().standardIcon(self.style().SP_CommandLink))
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.clicked.connect(self.send_message)
        
        # Status label
        self.status_label = QLabel("")
        
        # Assemble input layout
        self.input_layout.addWidget(self.prompt_label)
        self.input_layout.addWidget(self.prompt_text)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.send_button)
        
        self.input_layout.addLayout(button_layout)
        self.input_layout.addWidget(self.status_label)
        
        self.input_widget.setLayout(self.input_layout)
        
        # Add widgets to main layout
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.scroll_area)
        self.splitter.addWidget(self.input_widget)
        self.splitter.setSizes([500, 200])
        
        self.main_layout.addWidget(self.splitter)
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        
        # Set up theme menu
        self.create_menu()
        
        # Apply dark theme by default
        self.apply_theme(is_dark=True)
        
        # Set up signals
        self.worker_signals = WorkerSignals()
        self.worker_signals.finished.connect(self.process_response)
        self.worker_signals.error.connect(self.show_error)
    
    def create_menu(self):
        # Create menu bar
        menu_bar = self.menuBar()
        
        # Create Theme menu
        theme_menu = menu_bar.addMenu("Theme")
        
        # Create actions
        light_action = QAction("Light Theme", self)
        dark_action = QAction("Dark Theme", self)
        
        # Connect actions
        light_action.triggered.connect(lambda: self.apply_theme(is_dark=False))
        dark_action.triggered.connect(lambda: self.apply_theme(is_dark=True))
        
        # Add actions to menu
        theme_menu.addAction(light_action)
        theme_menu.addAction(dark_action)
    
    def apply_theme(self, is_dark=False):
        self.is_dark_theme = is_dark
        
        if is_dark:
            # Dark theme stylesheet
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #222222;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border-bottom: 1px solid #3d3d3d;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 5px 10px;
                }
                QMenuBar::item:selected {
                    background-color: #3a3a3a;
                    border-radius: 4px;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                }
                QMenu::item:selected {
                    background-color: #3a3a3a;
                }
                QScrollArea, QSplitter, QWidget#chat_widget {
                    background-color: #1e1e1e;
                    border: none;
                }
                QLabel {
                    font-size: 15px;
                    color: #dddddd;
                }
                QTextEdit {
                    border-radius: 8px;
                    border: 1px solid #3d3d3d;
                    padding: 8px;
                    background-color: #2d2d2d;
                    color: #ffffff;
                    selection-background-color: #3d5c99;
                    font-size: 15px;
                }
                QPushButton {
                    background-color: #3d5c99;
                    color: white;
                    border-radius: 18px;
                    padding: 10px 20px;
                    font-weight: bold;
                    border: none;
                    min-width: 100px;
                    min-height: 36px;
                    font-size: 15px;
                }
                QPushButton:hover {
                    background-color: #496db9;
                }
                QPushButton:pressed {
                    background-color: #2d4c89;
                }
                QSplitter::handle {
                    background-color: #3d3d3d;
                    height: 2px;
                }
                QScrollBar:vertical {
                    border: none;
                    background-color: #2d2d2d;
                    width: 12px;
                    margin: 12px 0 12px 0;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #3d3d3d;
                    min-height: 30px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #4d4d4d;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 12px;
                    background: none;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
            """)
            
            # Style the chat widget background
            self.chat_widget.setStyleSheet("background-color: #1e1e1e;")
            
            # Style the input widget
            self.input_widget.setStyleSheet("background-color: #1e1e1e; border-radius: 12px; border: 1px solid #3d3d3d;")
            
            # Style the status label
            self.status_label.setStyleSheet("color: #aaaaaa; font-style: italic;")
        else:
            # Light theme stylesheet - with darker trim
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #e8e8e8;
                }
                QMenuBar {
                    background-color: #e0e0e0;
                    border-bottom: 1px solid #cccccc;
                }
                QMenuBar::item {
                    padding: 5px 10px;
                }
                QMenuBar::item:selected {
                    background-color: #d0d0d0;
                    border-radius: 4px;
                }
                QMenu {
                    background-color: #f0f0f0;
                    border: 1px solid #cccccc;
                }
                QMenu::item:selected {
                    background-color: #e0e0e0;
                }
                QScrollArea, QSplitter {
                    background-color: #f0f0f0;
                    border: none;
                }
                QLabel {
                    font-size: 15px;
                    color: #444444;
                }
                QTextEdit {
                    border-radius: 8px;
                    border: 1px solid #c0c0c0;
                    padding: 8px;
                    background-color: #ffffff;
                    color: #333333;
                    selection-background-color: #c2e0ff;
                    font-size: 15px;
                }
                QPushButton {
                    background-color: #5c85d6;
                    color: white;
                    border-radius: 18px;
                    padding: 10px 20px;
                    font-weight: bold;
                    border: none;
                    min-width: 100px;
                    min-height: 36px;
                    font-size: 15px;
                }
                QPushButton:hover {
                    background-color: #4a6db3;
                }
                QPushButton:pressed {
                    background-color: #3d5c99;
                }
                QSplitter::handle {
                    background-color: #cccccc;
                    height: 2px;
                }
                QScrollBar:vertical {
                    border: none;
                    background-color: #e0e0e0;
                    width: 12px;
                    margin: 12px 0 12px 0;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #b0b0b0;
                    min-height: 30px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #999999;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 12px;
                    background: none;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
            """)
            
            # Style the chat widget background
            self.chat_widget.setStyleSheet("background-color: #f0f0f0;")
            
            # Style the input widget
            self.input_widget.setStyleSheet("background-color: #f0f0f0; border-radius: 12px; border: 1px solid #d5d5d5;")
            
            # Style the status label
            self.status_label.setStyleSheet("color: #888888; font-style: italic;")
    
    def send_message(self):
        prompt = self.prompt_text.toPlainText().strip()
        if not prompt:
            return
            
        # Show the user message
        self.add_message(prompt, is_user=True)
        
        # Clear the input field
        self.prompt_text.clear()
        
        # Update status
        self.status_label.setText("Thinking...")
        
        # Create a worker thread for API call
        worker = AnthropicWorker(prompt, self.message_history, self.worker_signals)
        worker.daemon = True
        worker.start()
        
    @Slot(str)
    def process_response(self, response_text):
        # Add the response to the chat
        self.add_message(response_text, is_user=False)
        
        # Clear status
        self.status_label.setText("")
        
    @Slot(str)
    def show_error(self, error_text):
        self.status_label.setText(f"Error: {error_text}")
        if self.is_dark_theme:
            self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
    def add_message(self, message: str, is_user: bool = False):
        # Add message to UI
        message_widget = MessageWidget(message, is_user, self.is_dark_theme)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message_widget)
        
        # Add message to history
        role = "user" if is_user else "assistant"
        self.message_history.append({"role": role, "content": message})
        
        # Scroll to bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show the window
    window = ChatBotWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
