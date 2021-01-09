'''
Created on 2019/04/11
@author: E9981231
'''
from PyQt5 import uic,  QtWidgets

import sys

Exit_Window_File = "../UI/Exit.ui" 
Ui_Exit, QtBaseClass = uic.loadUiType(Exit_Window_File)

class Exit_Window(QtWidgets.QDialog,Ui_Exit):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        super(Exit_Window,self).__init__()
        self.setupUi(self)
        

            
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Exit_Window()
    window.show()
    sys.exit(app.exec_())