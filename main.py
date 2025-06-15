import sys
from PyQt5.QtWidgets import QApplication
from controller.app_controller import AppController

def main():
    app = QApplication(sys.argv)
    controller = AppController(app)
    controller.run()

if __name__ == "__main__":
    main()
