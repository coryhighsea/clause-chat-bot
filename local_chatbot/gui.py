import sys
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QTextEdit, QPushButton, QLineEdit,
                             QHBoxLayout, QLabel, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from model_handler import ModelHandler

# Create a signal class for thread communication
class WorkerSignals(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

# Worker thread to handle API requests
class ModelWorker(threading.Thread):
    def __init__(self, model_handler, prompt, model_name, signals):
        super().__init__()
        self.model_handler = model_handler
        self.prompt = prompt
        self.model_name = model_name
        self.signals = signals
        
    def run(self):
        try:
            # Set the model name if needed
            if self.model_name != self.model_handler.model_name:
                self.model_handler.model_name = self.model_name
                
            # Get response from model
            response = self.model_handler.get_response(self.prompt)
            
            # Emit finished signal with the response
            self.signals.finished.emit(response)
        except Exception as e:
            # Emit error signal
            self.signals.error.emit(str(e))

class ChatbotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Local LLM Chatbot - Ollama API")
        self.setGeometry(100, 100, 800, 600)  # Adjust size as needed
        self.setStyleSheet("background-color: #1E1E1E; color: #ADD8E6;") # Dark theme
        
        # Initialize the model handler
        self.model_handler = ModelHandler()
        
        # Initialize worker signals
        self.worker_signals = WorkerSignals()
        self.worker_signals.finished.connect(self.handle_response)
        self.worker_signals.error.connect(self.handle_error)
        
        # Initialize current worker
        self.current_worker = None
        
        self.init_ui()
        
    def init_ui(self):
        # Create the main layout
        main_layout = QVBoxLayout()
        
        # Create the model selection area
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setStyleSheet("color: #ADD8E6;")
        self.model_selector = QComboBox()
        self.model_selector.setStyleSheet("background-color: #333333; color: #ADD8E6; padding: 5px;")
        self.populate_model_selector()
        model_refresh = QPushButton("Refresh")
        model_refresh.setStyleSheet("background-color: #333333; padding: 5px;")
        model_refresh.clicked.connect(self.populate_model_selector)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_selector, 1)
        model_layout.addWidget(model_refresh)
        
        # Chat history display
        self.response_window = QTextEdit()
        self.response_window.setReadOnly(True)
        self.response_window.setStyleSheet("background-color: #2D2D2D; border: 1px solid #555555; padding: 10px;")
        
        # Create the prompt input area
        prompt_layout = QHBoxLayout()
        self.prompt_window = QTextEdit()
        self.prompt_window.setStyleSheet("background-color: #2D2D2D; border: 1px solid #555555; padding: 10px;")
        self.prompt_window.setFixedHeight(100)
        
        # Enable Enter key to send message
        self.prompt_window.installEventFilter(self)
        
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("background-color: #0078D4; color: white; padding: 10px; border: none;")
        self.send_button.clicked.connect(self.send_message)
        
        prompt_layout.addWidget(self.prompt_window, 4)
        prompt_layout.addWidget(self.send_button, 1)
        
        # Status indicator
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888888; font-style: italic;")
        
        # Add everything to the main layout
        main_layout.addLayout(model_layout)
        main_layout.addWidget(self.response_window, 3)
        main_layout.addLayout(prompt_layout, 1)
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
        
        # Welcome message
        self.response_window.append("Welcome to the Local LLM Chatbot!")
        self.response_window.append("Using Ollama API for inference.")
        self.response_window.append("Type a prompt below and click Send.\n")
        
    def eventFilter(self, obj, event):
        if obj is self.prompt_window and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.NoModifier:
                self.send_message()
                return True
            elif event.key() == Qt.Key_Return and event.modifiers() == Qt.ShiftModifier:
                # Allow Shift+Enter for new lines
                return False
        return super().eventFilter(obj, event)
        
    def populate_model_selector(self):
        """Fetch available models from Ollama and populate the dropdown."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags")
            
            if response.status_code == 200:
                # Save the current selection
                current_selection = self.model_selector.currentText()
                
                # Clear the dropdown
                self.model_selector.clear()
                
                # Add available models with their full names including tags
                models = response.json().get("models", [])
                model_names = [model.get("name") for model in models]
                
                for model in model_names:
                    self.model_selector.addItem(model)
                
                # Restore selection if possible
                index = self.model_selector.findText(current_selection)
                if index >= 0:
                    self.model_selector.setCurrentIndex(index)
                elif self.model_selector.count() > 0:
                    self.model_selector.setCurrentIndex(0)
                    
                # Update the model handler with the selected model
                selected_model = self.model_selector.currentText()
                if selected_model:
                    self.model_handler.model_name = selected_model
                
            else:
                self.response_window.append(f"Error fetching models: Status code {response.status_code}")
                
        except Exception as e:
            self.response_window.append(f"Error connecting to Ollama API: {str(e)}")
            self.response_window.append("Make sure Ollama is running ('ollama serve')")

    def send_message(self):
        prompt_text = self.prompt_window.toPlainText()
        if prompt_text.strip() and not self.current_worker:
            # Display user message
            self.response_window.append(f"\nYou: {prompt_text}\n")
            self.prompt_window.clear()
            
            # Update status indicator
            self.status_label.setText("Thinking...")
            self.send_button.setEnabled(False)
            
            # Get selected model
            selected_model = self.model_selector.currentText()
            
            # Create and start worker thread
            self.current_worker = ModelWorker(
                self.model_handler, 
                prompt_text,
                selected_model,
                self.worker_signals
            )
            self.current_worker.start()
    
    def handle_response(self, response):
        """Handle successful response from the model."""
        # Clear status
        self.status_label.setText("")
        self.send_button.setEnabled(True)
        
        # Display response
        selected_model = self.model_selector.currentText()
        self.response_window.append(f"{selected_model}: {response}\n")
        
        # Scroll to bottom
        self.response_window.verticalScrollBar().setValue(
            self.response_window.verticalScrollBar().maximum()
        )
        
        # Reset worker
        self.current_worker = None
        
    def handle_error(self, error_msg):
        """Handle error from the model."""
        # Clear status
        self.status_label.setText("")
        self.send_button.setEnabled(True)
        
        # Display error
        self.response_window.append(f"Error: {error_msg}\n")
        self.response_window.append("Please ensure Ollama is running with 'ollama serve'\n")
        
        # Scroll to bottom
        self.response_window.verticalScrollBar().setValue(
            self.response_window.verticalScrollBar().maximum()
        )
        
        # Reset worker
        self.current_worker = None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = ChatbotGUI()
    gui.show()
    sys.exit(app.exec_())