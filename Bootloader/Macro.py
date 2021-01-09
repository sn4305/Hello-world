ID_Mode_request_OBC     = 0x4D0FF01     #Ask the OBC to enter/exit boot mode
ID_Mode_request_DCDC    = 0x4D3FF01  
ID_Security_Access      = 0x4E4FF01     #Exchange a fixed security key to validate the programming session
ID_Erase_Memory         = 0x4E0FF01     #Ask the addressed ECU to erase its internal application memory
ID_Transfer_INFO        = 0x4E1FF01     #Send memory identification, sequence counter, address and size of data to be programmed
ID_Transfer_DATA        = 0x4E2FF01     #Consecutive frames with sequence counter and data to be programmed
ID_CRC_request          = 0x4E3FF01     #Ask to perform a CRC check on the application memory
ID_Logistic_info_req    = 0x4E5FF01     #Ask for logistic information identified in the request

Boot_Mode_CMD           = 0x05
Default_Mode_CMD        = 0x06
Standby_Mode_CMD        = 0x00

Boot_Mode_CMD_Reply_ID  = 0xCFF03A0

Security_Access_Header  = [0x20]
Security_Access_Key     = [0x4D, 0x41, 0x52, 0x54, 0x45, 0x4B, 0x30]
Security_Access_CMD     = Security_Access_Header + Security_Access_Key

Erase_OBC_APP           = 0x20
Erase_OBC_HW_Ver        = 0x21          #Erase OBC hardware version ID
Erase_OBC_HW_SN         = 0x22          #Erase OBC hardware Serial number

'''
APPLI_PN_ADDRESS        = 0x02A3FA
APPCODE_START_ADDRESS   = 0x007000
APPCODE_END_ADDRESS     = 0x02A3FE
'''
APPLI_PN_ADDRESS        = 0x02A3FA
APPCODE_START_ADDRESS   = 0x003400
APPCODE_END_ADDRESS     = 0x02A3FE

CRC_IVT_SIZE_BYTE       = 0x300
CRC_APP_SIZE            = APPCODE_END_ADDRESS - APPCODE_START_ADDRESS
CRC_APP_SIZE_BYTE       = CRC_APP_SIZE*3/2

OBC_NUM                 = 1

import  can

class BOOT():
    def __init__(self,canif=None,CRC_Handler=None):
        self.canif = canif
        self.crc_handler = CRC_Handler
        
    def default_mode_request(self):
        ret = False
        D = [0]*8
        #send boot mode request        
        D[4] = Default_Mode_CMD              
        CAN_MSG = can.Message(arbitration_id = ID_Mode_request_OBC, data = D)
        self.canif.send(CAN_MSG)
        #recv with OverTime

        CAN_MSG = self.canif.recv(0.5)
        
        if CAN_MSG is None or CAN_MSG.dlc is not 8 or CAN_MSG.data[4] is not 0xC0:
            ret = False
        else:
            ret = True

        return ret
    '''
    def boot_mode_request(self):
        ret = False
        D = [0]*8
        #send boot mode request        
        D[4] = Boot_Mode_CMD              
        CAN_MSG = can.Message(arbitration_id = ID_Mode_request_OBC, data = D)
        self.canif.send(CAN_MSG)
        #recv with OverTime

        #Flash two OBC at the same time
        for _ in range(OBC_NUM):
            CAN_MSG = self.canif.recv(0.2)
            
            if CAN_MSG is None or CAN_MSG.dlc is not 8 or CAN_MSG.data[4] is not 0xC0:
                ret = False
                break
            else:
                ret = True

        return ret
    '''
    def boot_mode_request(self):
        ret = False
        D = [0]*8
        #send boot mode request        
        D[4] = Boot_Mode_CMD              
        CAN_MSG = can.Message(arbitration_id = ID_Mode_request_OBC, data = D)
        self.canif.send(CAN_MSG)
        #recv with OverTime

        #Flash two OBC at the same time
        for _ in range(5):
            CAN_MSG = self.canif.recv(0.2)
            
            if CAN_MSG is None or CAN_MSG.arbitration_id is not  Boot_Mode_CMD_Reply_ID:
                ret = False
                continue
            elif CAN_MSG.data[4] is 0xC0:
                ret = True
                return ret

        return ret
    
    def Security_Access_request(self):
        ret = False
        #send boot mode request                  
        CAN_MSG = can.Message(arbitration_id = ID_Security_Access, data = Security_Access_CMD)
        self.canif.send(CAN_MSG)
        #recv with OverTime

        for _ in range(OBC_NUM):
            CAN_MSG = self.canif.recv(0.2)
            if CAN_MSG is None or CAN_MSG.dlc is not 2 or CAN_MSG.data[0] is not Erase_OBC_APP:
                ret = False
                break
            elif CAN_MSG.data[1] == 0:
                ret = True

        return ret
    
    def Erase_request(self,ID=Erase_OBC_APP):
        ret = False
        #send boot mode request                  
        CAN_MSG = can.Message(arbitration_id = ID_Erase_Memory, data = [ID])
        self.canif.send(CAN_MSG)
        #recv with OverTime

        for _ in range(OBC_NUM):
            CAN_MSG = self.canif.recv()
            if CAN_MSG is None or CAN_MSG.dlc is not 2 or CAN_MSG.data[0] is not ID or CAN_MSG.data[1] is not 0x00:
                ret = False
                break
            else:
                ret = True
        
        return ret
    
    def Transfer_INFO_request(self, Area, Block_Cnt, Addr, Size):
        ret = False
        D = [0]*8
        D[0] = Area
        D[1] = Block_Cnt
        
        D[4] = Addr & 0xff        #low byte address
        D[3] = Addr>>8 & 0xff
        D[2] = Addr>>16 & 0xff    #high byte address
        
        D[6] = Size & 0xff        #low byte Size
        D[5] = Size>>8 & 0xff     #high byte Size
        
        #send boot mode request                  
        CAN_MSG = can.Message(arbitration_id = ID_Transfer_INFO, data = D)
        self.canif.send(CAN_MSG)
        #recv with OverTime
        
        for _ in range(OBC_NUM):
            CAN_MSG = self.canif.recv(0.05)
            if CAN_MSG is not None:
                ret = False
                break
            else:
                ret = True
        
        return ret
    
    '''
    param SN: Sequence Number, 1h ~ 25h
    type SN: int
    param data: length: 7 bytes
    type data: list
    '''
    def Transfer_DATA_request(self, SN, data):
        ret = False
        D = [0]*8
        D[0] = SN
        if len(data) > 7:
            raise
            return False
        else:
            D[1:] = data
            
        #send boot mode request                  
        CAN_MSG = can.Message(arbitration_id = ID_Transfer_DATA, data = D)
        self.canif.send(CAN_MSG)
        #recv with OverTime
        
        for _ in range(OBC_NUM):
            CAN_MSG = self.canif.recv(0.005)
            if CAN_MSG is None:
                if SN is 0x25:
                    ret = False
                    break
                else:
                    ret = True
            elif CAN_MSG.data[1] is not 0x00:
                ret = False
                break
            else:
                ret = True
        
        return ret
    
    def Req_Info_CRC(self, Area, Addr, Size):
        src = []
        src.append(Area)
        src.append(Addr>>16 & 0xff)
        src.append(Addr>>8 & 0xff)
        src.append(Addr & 0xff)
        src.append(Size>>8 & 0xff)
        src.append(Size & 0xff)
        return self.crc_handler.calculate(bytes(src))
    
    #program integration CRC verifying
    def Req_CRC(self, Hex):
        ret = False
        IVT_Data_real = [0xff]*6
        APP_Data_real = []

        if Hex.segments[0].start_address%0x800 is not 0 or Hex.segments[1].start_address%0x800 is not 0:
            print('Hex Format error(Addr is not aligned with 0x400)')
            return ret
        L = Hex.segments[0].size//4
        for _ in range(L):
            if _ == 0 or _ == 1:
                continue
            IVT_Data_real += Hex.segments[0].data[_*4:_*4+3]
        Pad_len = CRC_IVT_SIZE_BYTE - L*3
        IVT_Data_real += [0xff]*Pad_len
        CRC = self.crc_handler.calculate(bytes(IVT_Data_real))
        
        L = Hex.segments[1].size//4
        for _ in range(L):
            APP_Data_real += Hex.segments[1].data[_*4:_*4+3]

        Pad_len = int(CRC_APP_SIZE_BYTE - L*3 )
        APP_Data_real += [0xff]*Pad_len
        CRC = self.crc_handler.calculate(bytes(APP_Data_real),init_value=CRC)
        
        D = []
        D.append(Erase_OBC_APP)
        D.append((CRC >> 8) & 0xff)
        D.append(CRC & 0xff)
        
        #send boot mode request                  
        CAN_MSG = can.Message(arbitration_id = ID_CRC_request, data = D)
        self.canif.send(CAN_MSG)
        
        #recv with OverTime
        for _ in range(OBC_NUM):
            CAN_MSG = self.canif.recv(1)
            if CAN_MSG is None or  CAN_MSG.data[1] is not 0x00:
                ret = False
                break
            else:
                ret = True
        
        return ret