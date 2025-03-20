import sys
from PyQt5.QtWidgets import QApplication
from gui import ChatbotGUI

def main():
    """Main entry point for the chatbot application."""
    app = QApplication(sys.argv)
    gui = ChatbotGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()