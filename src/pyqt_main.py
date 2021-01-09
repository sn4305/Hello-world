# -*- coding:utf-8 -*-
#  pyqt_main.py
#
#  ~~~~~~~~~~~~
#
#  CAN Monitor for OBC debug based on ZLG USBCAN 200U
#
#  ~~~~~~~~~~~~
#
#  ------------------------------------------------------------------
#  Author : Dongdong Yang    
#  First change: 12.08.2019
#  Last change: 1.7.2021
#  Language: Python 3.6
#  ------------------------------------------------------------------
#
import sys, os
from PyQt5 import uic
from PyQt5.QtCore import Qt, QThread , QTimer
from PyQt5.QtGui import QPixmap,QPalette
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QApplication, QTableWidgetItem, QFileDialog
from Conf_Window import Conf_Window
from About import About_Window
from Password import Password_Window
from Scope import Scope_Window
from zlgcan import *
from dbc import dbc
from signals import SignalByteOrder
from InternalCAN import *  #need adapt this name when changed DBC name
from fileinput import close
import csv
import threading
import time, logging
import can
from can import Message

RED_LED = "../UI/Red.JPG"
GREEN_LED = "../UI/Green.JPG"
qtCreatorFile = "../UI/OBC Monitor_MainWindow.ui" # Enter file here.

CAN_BOX = ZCAN_USBCANFD_200U
MAX_DISPLAY = 1000

log = logging.getLogger('main')

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

###############################################################################
def Raw2Phy(S):
    return S.initial_value * S.factor - S.offset

class SendThread(QThread):
    def __init__(self,Period_func):
        super(SendThread,self).__init__()
        self._fun = Period_func
        self._SendFlag = False
        self._RunFlag = True
        self._period = 0.1
#         self.complete = pyqtSignal()
            
    def start_send(self,p=0.1):
        self._period = p
        self._SendFlag = True
        
    def stop_send(self):
        self._SendFlag = False
    
    def stop_thread(self):
        self._RunFlag = False
        
    def run(self):
        while self._RunFlag:
            if self._SendFlag:
                self._fun()
                time.sleep(self._period)
        
class MyApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MyApp,self).__init__()
        self.setupUi(self)
        self.statusBar.showMessage("Status...",3)
        self.tableWidget.setColumnWidth(0,20)
        self.tableWidget.setColumnWidth(1,10)
        self.tableWidget.setColumnWidth(2,15)
        self.tableWidget.setColumnWidth(3,160)
        self.tableWidget.setColumnWidth(4,220)
        self.tableWidget.current_row = 0
        self.tableWidget.MAX_ROW = 100
        self.tableWidget.show()
        
        '''    Banding            '''
        self.actionAbout.triggered.connect(self.Open_About)
        self.actionExit.triggered.connect(self.Exit)
        self.actionDownload.triggered.connect(lambda: self.Open_Load_MemWR(0))
        self.actionMemory_WR.triggered.connect(lambda: self.Open_Load_MemWR(1))
        self.actionScope.triggered.connect(self.Open_Scope)
        self.actionConnect.triggered.connect(self.Open_Device)
        
        self.Btn_SaveLog.clicked.connect(self.Slot_Btn_SaveLog)
        self.Btn_SaveCANFrame.clicked.connect(self.Slot_Btn_SaveCANFrame)
        self.Btn_StartStop.clicked.connect(self.Slot_Btn_StartStop)
        self.Btn_Clear.clicked.connect(self.Slot_Btn_Clear)
        self.Btn_W.clicked.connect(self.Slot_Btn_W)
        
        self._is_sending = False
        self._isChnOpen = False
        self.Open_Device()
             
    def Open_Load_MemWR(self, entry):
        self.pswd = Password_Window()
        self.pswd.pswd_entry = entry
        if entry == 0:
            self.pswd.canif = self.CAN
            self.pswd.Load.TrigSig.connect(self.Slot_Sig_Load_Trigger)
        self.pswd.show()
        
    def Open_Conf(self):
        self.Conf = Conf_Window()
        #banding Conf_Window's OK button to self.Slot_Btn_Conf_OK
        self.Conf.buttonBox.accepted.connect(self.Slot_Btn_Conf_OK)
        self.Conf.show()
        
    def Open_Scope(self):
        self.Scope = Scope_Window()
        self.Scope.TrigSig.connect(self.Slot_Btn_StartStop)
        self.Scope.show()
        
    def Open_About(self):
        self.About = About_Window()
        self.About.show()
        
    def Exit(self):
        self.close()
        
    ''' 
    Function: Transfer signal value to message;
    Parameter: 
        M:  CAN message
        S:  CAN signal
        TODO: add Intel format parser 
    '''
    def Signal2Msg(self, M, S):
        if S.initial_value > 2**S.bitlength:
            log.error("S.initial_value over field")
            return
        # if S.byteorder is SignalByteOrder.INTEL:
        #     log.error("Don't support Intel format now!")

        mask = 0   # restore signal valid bit
        mask = (2**S.bitlength - 1) << S.Shift_Bits
        mask = ~mask

        y = 0
        for i in range(8):
            y = y | (M[i] << (56 - 8*i))
        y = y & mask

        x = 0
        x = S.initial_value << S.Shift_Bits
        x = x | y

        for i in range(8):
            M[i] = 0xff & (x >> (56 - 8*i))
    
    ''' 
    Function: Transfer source message's data to target message's signal value;
    Parameter: 
        M: CAN message recv from CAN box

    '''
    def Msg2Signal(self, M):
        
        for m_t in dbc[0].messages:
            try:
                if m_t.ID == M.arbitration_id and 'OBC_1' == m_t.sender:
                    '''copy received can data to global can data base'''
                    m_t.Frame = M
                    '''transform can message data to signal raw value'''
                    candata = 0
                    i = 56
                    for d in m_t.Frame.data:
                        if i >= 0:
                            candata = candata | (d << i)
                            i -= 8
                    for s in m_t.signals:
                        s.initial_value = (candata >> s.Shift_Bits) % (2**s.bitlength)
            except:
                log.error("Msg2Signal exception!")

    def Slot_Btn_W(self):
        ID_0x4d0a001__OBC_ChargingModeRequest.initial_value = self.comboBox_Phs.currentIndex()
        log.debug("set %s value: %s" %(ID_0x4d0a001__OBC_ChargingModeRequest.name, self.comboBox_Phs.currentText()))
        self.textEdit.append("set ChargingMode: %s" %self.comboBox_Phs.currentText())
        ID_0x4d0a001__OBC_ModeRequest.initial_value = self.comboBox_OPMODE.currentIndex()
        log.debug("set %s value: %s" %(ID_0x4d0a001__OBC_ModeRequest.name, self.comboBox_OPMODE.currentText()))
        self.textEdit.append("set ModeRequest: %s" %self.comboBox_OPMODE.currentText())
        try:
            if self.lineEdit_Vout.text() is not None:
                ''' Assert and Change signal value '''
                if float(self.lineEdit_Vout.text()) <= ID_0x4d0a001__OBC_SetPointV.maximum and \
                    float(self.lineEdit_Vout.text()) >= ID_0x4d0a001__OBC_SetPointV.minimum:
                    ID_0x4d0a001__OBC_SetPointV.initial_value = \
                        int((ID_0x4d0a001__OBC_SetPointV.offset + float(self.lineEdit_Vout.text()))/ID_0x4d0a001__OBC_SetPointV.factor)
                    log.debug("set %s value: %s" %(ID_0x4d0a001__OBC_SetPointV.name, self.lineEdit_Vout.text()))
                    self.textEdit.append("set SetPointV: %s V" %self.lineEdit_Vout.text())
        except:
            log.debug("Slot_Btn_W_Vout exception!")

        try:
            if self.lineEdit_Iout.text() is not None:
                ''' Assert and Change signal value '''
                if float(self.lineEdit_Iout.text()) <= ID_0x4d0a001__OBC_SetPointI.maximum and \
                    float(self.lineEdit_Iout.text()) >= ID_0x4d0a001__OBC_SetPointI.minimum:
                    ID_0x4d0a001__OBC_SetPointI.initial_value = \
                        int((ID_0x4d0a001__OBC_SetPointI.offset + float(self.lineEdit_Iout.text()))/ID_0x4d0a001__OBC_SetPointI.factor)
                    log.debug("set %s value: %s" %(ID_0x4d0a001__OBC_SetPointI.name, self.lineEdit_Iout.text()))
                    self.textEdit.append("set SetPointI: %s A" %self.lineEdit_Iout.text())
        except:
            log.debug("Slot_Btn_W_Iout exception!") 
                                
        
    def Slot_Btn_SaveLog(self):    
        try:
            fileName_choose, filetype = QFileDialog.getSaveFileName(self,  
                                    "Save log file",  
                                    '../Log/',
                                    "All Files (*)")   
    
            log.info("file type is: ",filetype)
            log.info("file dir is: ",fileName_choose)
            with open(fileName_choose,'w') as f:
                logger = self.textEdit.toPlainText()
                f.write(logger)
            self.textEdit.append(fileName_choose + ' have been saved.')
        except:
            log.error("open file error!")
            
    def Slot_Btn_SaveCANFrame(self):
        try:
            fileName_choose, filetype = QFileDialog.getSaveFileName(self,  
                                    "Save CAN Frame log",  
                                    '../Log',
                                    ".csv Files (*.csv);;All Files (*)")   
    
            log.info("file type is: ",filetype)
            with open(fileName_choose,'w',newline='') as f:
                row = []
                writer = csv.writer(f)
                writer.writerow(['CAN_ID','DIR','DLC','DATA','TimeStamp'])
                for n in range(self.tableWidget.current_row):
                    for i in range(5):
                        row.append(self.tableWidget.item(n,i).text())
                    writer.writerow(row)
                    row.clear()
            self.textEdit.append(fileName_choose + ' have been saved.')
        except:
            log.error("open file error!")
            
    def Slot_Btn_Clear(self):
        x = self.tableWidget.current_row
        self.tableWidget.current_row = 0
        self.textEdit.append('Clear CAN Frame window.')
        while x > 0:
            self.tableWidget.removeRow(0)
            x = x - 1
        
    def Slot_Btn_StartStop(self):
        try:
            if self._is_sending == True:
                if self.Btn_StartStop.text() == 'Start':
                    self.Btn_StartStop.setText("Stop")
                    self._send_thread.start_send(0.01) #10ms period
                    self.CANRecvEvent.set()
                    self.flsTim.start(500)
                    self.textEdit.append("Start CAN Tx/Rx.")
    
                elif self.Btn_StartStop.text() == 'Stop':
                    self.Btn_StartStop.setText("Start")
                    self._send_thread.stop_send()
                    self.CANRecvEvent.clear()
                    self.flsTim.stop()
                    self.textEdit.append("Stop CAN Tx/Rx.")
                    
#                 self.textEdit.append("Scope signal Trigged, stop sending...")
            else:
                self.textEdit.append("Can't start can tx/rx, please Open CAN Box first!")

            pass
        except:
            log.error("Slot_Btn_StartStop: Error!")
            pass  

    def Refresh_View(self):
        # Refresh OBC info
        V = Raw2Phy(ID_0xcff01a0__OBC_Vin_ph1)
        self.lineEdit_VinA.setText(str(V))
        V = Raw2Phy(ID_0xcff01a0__OBC_Vin_ph2)
        self.lineEdit_VinB.setText(str(V))
        V = Raw2Phy(ID_0xcff01a0__OBC_Vin_ph3)
        self.lineEdit_VinC.setText(str(V))

        I = Raw2Phy(ID_0xcff02a0__OBC_Iin_ph1)
        self.lineEdit_IinA.setText(str(I))
        I = Raw2Phy(ID_0xcff02a0__OBC_Iin_ph2)
        self.lineEdit_IinB.setText(str(I))
        I = Raw2Phy(ID_0xcff02a0__OBC_Iin_ph3)
        self.lineEdit_IinC.setText(str(I))

        I = Raw2Phy(ID_0xcff00a0__OBC_Iout)
        self.lineEdit_Iout_R.setText(str(I))

        V = Raw2Phy(ID_0xcff05a0__OBC_PFC_VOLTAGE_PH1)
        self.lineEdit_VbusA.setText(str(V))
        V = Raw2Phy(ID_0xcff05a0__OBC_PFC_VOLTAGE_PH2)
        self.lineEdit_VbusB.setText(str(V))
        V = Raw2Phy(ID_0xcff05a0__OBC_PFC_VOLTAGE_PH3)
        self.lineEdit_VbusC.setText(str(V))

        V = Raw2Phy(ID_0xcff00a0__OBC_Vout)
        self.lineEdit_Vout_R.setText(str(V))

        self.comboBox_Status.setCurrentIndex(ID_0xcff03a0__OBC_Status.initial_value)        

        P = Raw2Phy(ID_0xcff00a0__OBC_Power)
        self.lineEdit_Pwr.setText(str(P))

        T = Raw2Phy(ID_0xcff04a0__OBC_TempSensor)
        self.lineEdit_Tenv.setText(str(T))
        T = Raw2Phy(ID_0xcff04a0__OBC_TempCTN)
        self.lineEdit_Tims.setText(str(T))
        T = Raw2Phy(ID_0xcff04a0__OBC_TempMax)
        self.lineEdit_Tmax.setText(str(T))
        #Error info
        self.chkBox_ErrorUVPVout.setCheckState(ID_0xcff03a0__OBC_ErrorUVPVout.initial_value)
        self.chkBox_ErrorOVPVout.setCheckState(ID_0xcff03a0__OBC_ErrorOVPVout.initial_value)
        self.chkBox_ErrorUVPVin.setCheckState(ID_0xcff03a0__OBC_ErrorUVPVin.initial_value)
        self.chkBox_ErrorCANframePeriod.setCheckState(ID_0xcff03a0__OBC_ErrorCANframePeriod.initial_value)

    def Slot_Sig_Load_Trigger(self):
        if self._is_sending == True:
            if self.Btn_StartStop.text() == 'Stop':
                self.Btn_StartStop.setText("Start")
                self._send_thread.stop_send()
                self.CANRecvEvent.clear()
                self.textEdit.append("Stop CAN Tx/Rx.")
            
    def CANDataUpdate(self, msg, is_send=True):
        with self._Rlock:
            try:
                from datetime import datetime
                if self.tableWidget.current_row < self.tableWidget.MAX_ROW:
                    x = self.tableWidget.current_row                
                else:
                    x = self.tableWidget.MAX_ROW - 1
                    self.tableWidget.removeRow(0)  # remove first Row
                    
                self.tableWidget.insertRow(x)  # add last Row
                self.tableWidget.verticalScrollBar().setSliderPosition(x)
                self.tableWidget.setItem(x, 0, QTableWidgetItem(str(hex(msg.arbitration_id))))  #ID
                self.tableWidget.setItem(x, 1, QTableWidgetItem('TX' if is_send==True else "RX"))  #DIR
                self.tableWidget.setItem(x, 2, QTableWidgetItem("8"))  #DLC
                self.tableWidget.setItem(x, 3, QTableWidgetItem(str(list(msg.data))))  #DATA
                self.tableWidget.setItem(x, 4, QTableWidgetItem(str(datetime.now())))  #TIMESTAMP
                self.tableWidget.current_row =  x + 1
            except:
                log.error("CANDataUpdate: Error Table Format!")
        
    def PeriodSend(self):
        self.TxLoad()
        try:
            for m in self._send_msgs:
                self.CAN.send(m)
            #update transmit display
                self.CANDataUpdate(m, True)
        except:
            log.error("PeriodSend: Transmit fail!")

    def MsgRead(self,event):
        try:
            while not self._terminated:
                ''' if clear, this thread will be blocked, else if set, this thread will run'''
                event.wait()
                m = self.CAN.recv(0.1)
                if m is not None:
                    self.Msg2Signal(m)
                    self.CANDataUpdate(m, False)
                    pass
        except:
            log.error("Error occurred while read CAN data!")
    
    def TxLoad(self):
        M = 8*[0]
        try:
            self._send_msgs.clear()
            for m in dbc[0].messages:
                if 'TxPGN_53408_ICAN_REQ_00100_ToOBC' == m.name or \
                    'Master_All_OBC' == m.name:
                    ''' pack signal value into message data field '''
                    for s in m.signals:
                        self.Signal2Msg(M, s)
                    m.Frame.data = bytearray(M)
                    self._send_msgs.append(m.Frame)
        except:
            log.error('TXLoad error')
        
    def Open_Device(self):
        if self._isChnOpen == False:
            try:
                self.CAN = can.Bus(interface='zlgcan')
                log.info("init can bus")
            except Exception as ex:
                self.textEdit.append(str(ex))
                return
            self._isChnOpen = True
            self.textEdit.append('---------------Open CAN box OK------------------')
            self.flsTim =  QTimer(self)
            self.flsTim.timeout.connect(self.Refresh_View)

            self._Rlock = threading.RLock()
            self._send_thread = SendThread(self.PeriodSend)
            self._send_thread.start()
            self._is_sending = True
            
            #start receive thread
            self._terminated = False
            self.CANRecvEvent = threading.Event()
            self.CANRecvEvent.clear()
            self._read_thread = threading.Thread(target=self.MsgRead, args = (self.CANRecvEvent,))
            self._read_thread.start()
            self._send_msgs = []         

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', 'You sure to quit?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
 
        if reply == QMessageBox.Yes:
#             #Stop Send Thread
            try:
                #Close Device
                if self._isChnOpen == True:
                    self.CAN.shutdown()
                    self._isChnOpen = False
                    
                if self._is_sending is True:
                    self._send_thread.stop_thread()
                    self._is_sending = False
                if self._terminated is False:
                    self._read_thread.join(1)  
                    self._terminated = True
                    self.CANRecvEvent.set()
                                        
            except:
                log.error("Can not close thread")
#                 return
            event.accept()
        else:
            event.ignore()
      
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
    