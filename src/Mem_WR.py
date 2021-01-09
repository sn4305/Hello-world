'''
Created on 2019/04/16

@author: E9981231
'''
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QMessageBox
import sys


MemWR_Window_File = "../UI/Memory WR.ui" 
Ui_MemWR, QtBaseClass = uic.loadUiType(MemWR_Window_File)


class MemWR_Window(QWidget,Ui_MemWR):
    def __init__(self):
        super(MemWR_Window,self).__init__()
        self.setupUi(self)
        self.Btn_Read.clicked.connect(self.Slot_Read)
        self.Btn_Write.clicked.connect(self.Slot_Write)
    
    
    def Slot_Read(self):
        try:
            Addr = self.lineEdit_Address.text()
            Val = self.lineEdit_Value.text()
            print('Read '+'Address '+Addr+'Value '+Val) 
            self.textEdit.append('Read: '+'Address '+Addr+', Value '+Val)
            
        except:
            print("error1") 
            
    def Slot_Write(self):
        try:
            Addr = self.lineEdit_Address.text()
            Val = self.lineEdit_Value.text()
            if Val:
                self.textEdit.append('Write: '+'Address '+Addr+', Value '+Val)
            else:
                self.textEdit.append('please input a Value!')
        except:
            print("error2")        
                 
    def MsgBox(self):   
        QMessageBox.warning(self, 'Warning', 'Address range error!')     
            
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MemWR_Window()
    window.show()
    sys.exit(app.exec_())
