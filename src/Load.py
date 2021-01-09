'''
Created on 2019/04/11

@author: E9981231
'''
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import  QApplication, QFileDialog, QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal
import sys,os
from yaml import emit
Load_Window_File = "../UI/Load.ui" 
Ui_Load, QtBaseClass = uic.loadUiType(Load_Window_File)

import udsoncan, isotp, logging
from udsoncan.client import Client
from udsoncan.services import *
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.exceptions import *
from S19_Parser import S19
from UDS_config import Myconfig
import queue


DEFAULT_LOADFILE_PATH = '../lib/Test.s19'
FLASH_BLOCK_SIZE = 0xF7
UDS_FRAME_PADDING = 0x55

udsoncan.setup_logging()

# logging.basicConfig(level=logging.DEBUG,filename='../Log/zlgcan.log')
class Thread_download(QtCore.QThread):
    progress_bar_trigger = pyqtSignal(int)
    label_trigger = pyqtSignal(str)
    msgBox_trigger = pyqtSignal(str,str)
    
    def __init__(self,canif,file=None):
        super(Thread_download,self).__init__()
        self.canif = canif
        self.file = file
        
    def run(self):
        try:
            if self.file is not None:
                if not os.path.exists(self.file):
                    print("\nfile error!")
                    raise
                    return
            
            self.label_trigger.emit('Start...')
            self.progress_bar_trigger.emit(0)

            if self.canif is not None:
                tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7E0, rxid=0x7E8) # Network layer addressing scheme
                stack = isotp.CanStack(bus=self.canif, address=tp_addr)               # Network/Transport layer (IsoTP protocol)
                stack.params.tx_padding = UDS_FRAME_PADDING
                UDSconn = PythonIsoTpConnection(stack)                                                 # interface between Application and Transport layer
                with Client(UDSconn, config=Myconfig, request_timeout=2) as client:
                    try:
                        self.label_trigger.emit('Parsing s19 file...')
                        srec = S19(block_size=FLASH_BLOCK_SIZE)
                        self.label_trigger.emit('Pre-Programming...')
                        self.step = 5
                        self.progress_bar_trigger.emit(self.step)
                        
                        #Pre-Programming step
                        #Session control-->extended session
                        client.change_session(DiagnosticSessionControl.Session.extendedDiagnosticSession)  # integer with value of 3
                        #Control DTC setting-->off
                        client.control_dtc_setting(ControlDTCSetting.SettingType.off)
                        #Communication Control-->disableRxAndTx in the application
                        client.communication_control(CommunicationControl.ControlType.disableRxAndTx,udsoncan.CommunicationType(0,normal_msg=True))
                        self.step = 10
                        self.progress_bar_trigger.emit(self.step)
                        
                        #Programming step
                        #Session control-->programmingSession
                        self.label_trigger.emit('Programming...')
                        client.change_session(DiagnosticSessionControl.Session.programmingSession)  # integer with value of 2
                        #SecurityAccess
                        
                        #RoutineControl-->erase memory, routine id: 0xFF00
                        client.routine_control(udsoncan.Routine.EraseMemory, RoutineControl.ControlType.startRoutine)
                        self.step = 15
                        self.progress_bar_trigger.emit(self.step)
                        module_num = len(srec.module)
                        for m in srec.module:
                            #RequestDownload
                            self.label_trigger.emit('request_download...')
                            client.request_download(udsoncan.MemoryLocation(m.address,m.length))
                            block_idx = 0x01
                            step_pix = 70/len(m.block)/module_num
                            #Transfer block data
                            for b in m.block:
                                self.label_trigger.emit('transfer_data...')
                                tmp = bytes.fromhex(b.data)
                                if tmp == False:
                                    raise
                                client.transfer_data(block_idx,tmp)
                                if module_num == 1:
                                    self.step += step_pix
                                    self.progress_bar_trigger.emit(self.step)
                                block_idx += 1
                            #Request Transfer exit
                            client.request_transfer_exit()
                        
                        #check programming dependencies
                        client.routine_control(udsoncan.Routine.CheckProgrammingDependencies, RoutineControl.ControlType.startRoutine)
                        #WriteDataById.VIN
                        client.write_data_by_identifier(udsoncan.DataIdentifier.VIN, 'ABCDE0123456789')
                        print('Vehicle Identification Number successfully changed.')
                        #Post-programming step --> ECU hardreset       
                        client.ecu_reset(ECUReset.ResetType.hardReset)  # HardReset = 0x01   
                        self.progress_bar_trigger.emit(100)
                        self.label_trigger.emit('Download Success!')
                        self.msgBox_trigger.emit("Info",'Download Finished!')
                        
                    except NegativeResponseException as e:
                        print('Server refused our request for service %s with code "%s" (0x%02x)' % (e.response.service.get_name(), e.response.code_name, e.response.code))
                    except (InvalidResponseException, UnexpectedResponseException) as e:
                        print('Server sent an invalid payload : %s' % e.response.original_payload)
                    except ValueError as e:
                        print('ValueError ')
                    
            
        except:
            self.msgBox_trigger.emit('error', 'Thread_download error ') 
            
class Load_Window(QWidget,Ui_Load):
    '''
    classdocs
    '''
    TrigSig = pyqtSignal()
    def __init__(self):
        '''
        Constructor
        '''
        super(Load_Window,self).__init__()
        self.setupUi(self)
        self.step = 0
        self.label_Status.setText(' ')
        self.canif = None
        self._thread = None
        #Bind
        self.btn_chooseFile.clicked.connect(self.slot_btn_chooseFile)
        self.btn_load.clicked.connect(self.download)
        
    def slot_btn_chooseFile(self):
        try:
            fileName_choose, filetype = QFileDialog.getOpenFileName(self,  
                                    "Choose file",  
                                    './',
                                    "Bin Files (*.s19);;All Files (*)")   
            if not os.path.exists(fileName_choose):
                print("\ncancel choose")
                return
    
            print("\nYour choice is:")
            print(fileName_choose)
            print("file type is: ",filetype)
            self.lineEdit.setText(fileName_choose)
        except:
            print("open file error!")

    def download(self):
        self.TrigSig.emit()
        print("into download!")
        self._thread = Thread_download(canif=self.canif,file=self.lineEdit.text())
        self._thread.progress_bar_trigger.connect(self.slot_progress_bar)
        self._thread.label_trigger.connect(self.slot_label)
        self._thread.msgBox_trigger.connect(self.MsgBox)
        self._thread.start()
        
    def slot_progress_bar(self,val):
        self.progressBar.setValue(val)
        
    def slot_label(self,str):
        self.label_Status.setText(str)

    def MsgBox(self,title,msg):   
        QMessageBox.warning(self, title, msg) 
        
if __name__ == "__main__":
    import can
    with can.Bus(interface='zlgcan') as CAN:
        app = QApplication(sys.argv)
        window = Load_Window()
        window.canif = CAN
        window.show()
        sys.exit(app.exec_())