'''
Created on 2019/04/11
@author: E9981231
'''
from PyQt5 import uic,  QtWidgets
from PyQt5.QtGui import QPixmap
import sys

About_Window_File = "../UI/About.ui" 
Eaton_logo_file = "../UI/Eaton.JPG"
Ui_About, QtBaseClass = uic.loadUiType(About_Window_File)


class About_Window(QtWidgets.QDialog,Ui_About):
    def __init__(self):
        super(About_Window,self).__init__()
        self.setupUi(self)
        try:
            pixmap = QPixmap(Eaton_logo_file)
            self.label_logo.setPixmap(pixmap)
        except:
            print("Can't find pic source!")
            
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = About_Window()
    window.show()
    sys.exit(app.exec_())