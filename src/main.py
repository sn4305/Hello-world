from PyQt5.QtWidgets import QApplication
from pyqt_main import MyApp
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())