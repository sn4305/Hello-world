'''
Created on 2019/04/11

@author: E9981231
'''
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import  QApplication, QFileDialog, QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal
import os
from sympy.logic.boolalg import false
from time import sleep
Load_Window_File = "Load.ui" 
Ui_Load, QtBaseClass = uic.loadUiType(Load_Window_File)

import udsoncan, isotp 

from udsoncan.client import Client
from udsoncan.services import *
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.exceptions import *
from S19_Parser import S19
from Hex_Parser import HexFile
from UDS_config import Myconfig
from Macro import *
from Macro import BOOT
from PyCRC import CRC16


DEFAULT_LOADFILE_PATH = '../lib/Test.s19'
FLASH_BLOCK_SIZE = 0xF8
UDS_FRAME_PADDING = 0x55

udsoncan.setup_logging('logging.conf')

# logging.basicConfig(level=logging.DEBUG,filename='../Log/zlgcan.log')
class Thread_download(QtCore.QThread):
    progress_bar_trigger = pyqtSignal(int)
    label_trigger = pyqtSignal(str)
    msgBox_trigger = pyqtSignal(str,str)
    
    def __init__(self,canif,file=None):
        super(Thread_download,self).__init__()
        self.canif = canif
        self.file = file
        self.crc_handler = CRC16.CRC16()
        
    def run(self):
        try:
            if self.file is not None:
                if not os.path.exists(self.file):
                    print("\nfile error!")
                    raise
                    return
                
                if self.canif is not None:
                    
                    if 'hex' in self.file:
                        Hex = HexFile.load(self.file)
                        
                        self.label_trigger.emit('into hex loading')
                        print(Hex.segments)
                        
                        B = BOOT(self.canif,self.crc_handler)
                        
                        Block_Size = 0x100
                        
                        
                        if B.boot_mode_request() is True:
#                             print("self.boot_mode_request() is True")
                            if B.Security_Access_request() is True:
#                                 print("self.Security_Access_request() is True")
                                if B.Erase_request() is True:
                                    self.step = 5
                                    self.progress_bar_trigger.emit(self.step)
                                    Block_Cnt = 0
                                    BN = 0
                                    self.label_trigger.emit('Tranferring IVT data...')
                                    S = 0
                                    for Seg in Hex.segments:                                        
                                        if Seg.size < 100:
                                            continue
                                        Block_Cnt += BN
                                        BN = 0
                                        if S is 1:
                                            self.step = 45
                                            self.progress_bar_trigger.emit(self.step)
                                            self.label_trigger.emit('Tranferring APP data...')
                                        while True:
                                            addr = Seg.start_address + BN * Block_Size
                                            if Seg.start_address + Block_Size * (BN + 1) <=  Seg.end_address:                                                              
                                                if B.Transfer_INFO_request(Erase_OBC_APP, BN, addr , Block_Size) is True: 
                                                    SN = 1   
                                                    
                                                    crc = B.Req_Info_CRC(Erase_OBC_APP, addr , Block_Size)   
                                                    #Calc CRC
                                                    src = Seg.data[BN*Block_Size :  (BN+1)*Block_Size]
                                                    crc = self.crc_handler.calculate(bytes(src),init_value=crc)                                                                                                               
                                                    #append crc to block data list                                                    
                                                    src.append(crc>>8 & 0xff)
                                                    src.append(crc&0xff)
                                                    
                                                    print("Seg[%1d].Block[%3d]  start address: 0x%-8x size:0x%03x      CRC:0x%04x" % (S, BN, addr, len(src)-2, crc ))                                      
                                                    while True:
                                                        if SN*7 < len(src):
                                                            if B.Transfer_DATA_request(SN, src[(SN-1)*7 : SN*7]) is False:
                                                                self.label_trigger.emit('Transfer_DATA_request  failed!')
                                                                return
                                                            
                                                        elif SN*7 == len(src):
                                                            if B.Transfer_DATA_request(SN, src[(SN-1)*7 : SN*7]) is False:  #last block frame
                                                                self.label_trigger.emit('Transfer_DATA_request  failed!')
                                                                return
                                                            break
                                                        
                                                        else:
                                                            if B.Transfer_DATA_request(SN, src[(SN-1)*7 : ]) is False:
                                                                self.label_trigger.emit('Transfer_DATA_request  failed!')
                                                                return
                                                            break
                                                        SN += 1
                                                    if Seg.start_address + Block_Size * (BN + 1) ==  Seg.end_address:
                                                        break
    #                                                     self.step = 50
    #                                                     self.progress_bar_trigger.emit(self.step)
                                                    BN += 1
                                                else:
                                                    self.label_trigger.emit('Transfer_INFO_request  failed!')
                                                    return
                                                    
                                            else:
                                                remain_size = Seg.end_address - (Seg.start_address + BN * Block_Size)
#                                                 print("remain_size: %d" % (remain_size))
                                                if B.Transfer_INFO_request(Erase_OBC_APP, BN, addr, remain_size) is True: 
                                                    SN = 1   
                                                    crc = B.Req_Info_CRC(Erase_OBC_APP, addr , remain_size)   
                                                    #Calc CRC
                                                    src = Seg.data[BN*Block_Size :  ]
                                                    crc = self.crc_handler.calculate(bytes(src),init_value=crc)                                                                                                               
                                                    #append crc to block data list
                                                    src.append(crc>>8 & 0xff)
                                                    src.append(crc&0xff)
                                                    
                                                    print("Seg[%1d].Block[%3d]  start address: 0x%-8x size:0x%03x      CRC:0x%04x" % (S, BN, addr, len(src)-2, crc ))                                            
                                                    while True:
                                                        if SN*7 < len(src):
                                                            if B.Transfer_DATA_request(SN, src[(SN-1)*7 : SN*7]) is False:
                                                                self.label_trigger.emit('Transfer_DATA_request  failed!')
                                                                return
                                                            
                                                        elif SN*7 == len(src):
                                                            if B.Transfer_DATA_request(SN, src[(SN-1)*7 : SN*7]) is False:  #last block frame
                                                                self.label_trigger.emit('Transfer_DATA_request  failed!')
                                                                return
                                                            break
                                                        
                                                        else:
                                                            if B.Transfer_DATA_request(SN, src[(SN-1)*7 : ]) is False:
                                                                self.label_trigger.emit('Transfer_DATA_request  failed!')
                                                                return
                                                            break
                                                        SN += 1
                                                    break
                                                else:
                                                    self.label_trigger.emit('Transfer_INFO_request  failed!')
                                                    return
                                        S += 1    
                                    self.step = 80
                                    self.progress_bar_trigger.emit(self.step)
                                    self.label_trigger.emit('Download OK! Checking CRC...')
                                    
                                    if B.Req_CRC(Hex) is True:
                                        self.step = 100
                                        self.progress_bar_trigger.emit(self.step)
                                        self.label_trigger.emit('CRC Verification Passed')
                                        
                                    else:
                                        self.label_trigger.emit('CRC Verification failed!') 
                                    
                                else:
                                    self.label_trigger.emit('Erase request failed!')    
                            else:
                                self.label_trigger.emit('Security Access failed!')        
                        else:
                            self.label_trigger.emit('Boot mode request failed!')      
                        
                        #clear CAN box recv buffer
                        
                        for _ in range(5):
                            self.canif.recv(0.1)
        
                        
                    elif 's19' in self.file:                              
                        self.label_trigger.emit('Start...')
                        self.progress_bar_trigger.emit(0)
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
                else:
                    self.msgBox_trigger.emit('error', ' CAN box not opened! ') 
            
        except:
            self.msgBox_trigger.emit('error', 'Thread_download error ') 
            
class Load_Window(QWidget,Ui_Load):
    '''
    classdocs
    '''
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
        self.filetype = None
        #Bind
        self.btn_chooseFile.clicked.connect(self.slot_btn_chooseFile)
        self.btn_load.clicked.connect(self.download)
        
        if os.path.exists('./tmp'):
            with open('./tmp','r') as rf:
                self.lineEdit.setText(rf.read())
        
    def slot_btn_chooseFile(self):
        try:
            fileName_choose, self.filetype = QFileDialog.getOpenFileName(self,  
                                    "Choose file",  
                                    './',
                                    "Hex Files (*.hex);;Bin Files (*.s19);;All Files (*)")   
            if not os.path.exists(fileName_choose):
                print("cancel choose")
                return
    
#             print("\nYour choice is:")
#             print(fileName_choose)
#             print("file type is: ",self.filetype)
            self.lineEdit.setText(fileName_choose)
            with open('./tmp','w') as wf:
                wf.write(fileName_choose)
        except:
            print("open file error!")

    def download(self):
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