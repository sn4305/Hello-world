'''
Created on 2019/04/15

@author: E9981231
'''

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox,QLineEdit
from Load import Load_Window
from Mem_WR import MemWR_Window
import sys

Load_Password = "123"
MemWR_Password = "123"
Password_Window_File = "../UI/Password.ui" 
Ui_Password, QtBaseClass = uic.loadUiType(Password_Window_File)


class Password_Window(QDialog,Ui_Password):
    def __init__(self):
        super(Password_Window,self).__init__()
        self.setupUi(self)
        self.lineEdit.setEchoMode(QLineEdit.Password)
        self.pswd_entry = None
        self.canif = None
        self.Load = Load_Window()
        
    def accept(self):
        try:
#             print('pswd_entry: ')
#             print(self.pswd_entry)  
            if self.pswd_entry ==0:
                if self.lineEdit.text() == Load_Password:
                    self.Load.canif = self.canif
                    self.Load.show()
                    self.close()
                else: 
                    print(self.lineEdit.text()) 
                    self.MsgBox()
                    
            elif self.pswd_entry ==1:
                if self.lineEdit.text() == MemWR_Password:
                    self.Mem = MemWR_Window()
                    self.Mem.show()
                    self.close()
                else: 
                    print(self.lineEdit.text()) 
                    self.MsgBox()
        except:
            print("error")       
         
    def MsgBox(self):   
        QMessageBox.warning(self, 'Warning', 'Wrong password!')     
            
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Password_Window()
    window.show()
    sys.exit(app.exec_())