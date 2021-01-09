from PyQt5 import  uic, QtWidgets
import sys


Conf_Window_File = "../UI/COM Config.ui" 
Ui_Dialog, QtBaseClass = uic.loadUiType(Conf_Window_File)



class Conf_Window(QtWidgets.QDialog,Ui_Dialog):
    def __init__(self):
        super(Conf_Window,self).__init__()
        self.setupUi(self)
#         self.CAN_CH = 0
        self.Machine_Model = None
        self.Machine_ID = None
        self.Machine_Version = None
        
    def accept(self):
#         self.timer = QtCore.QTimer(self) 
#         self.timer.timeout.connect(self.close)
#         self.timer.start(2000) 
#         self.label_Status.SetText("Connected!")
        self.close()


#     def reject(self):
# #         self.close()
#         print("no")
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Conf_Window()
    window.show()
    sys.exit(app.exec_())
