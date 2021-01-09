#coding:utf-8
import os
Addr = [0x1f,0x12,0x55,0x55,0xff,0xf2,0xf1,0]
'''
Usage: Transform CAN signal to CAN Data frame in Intel Byte order
Para: 
    Addr: CAN Data frame base address
    Val: real value tend to be loaded
    StartBit: Signal Start bit
    ll: Signal length


from _datetime import time
def Signal2Msg(Addr, Val, StartBit, ll):
    if Val > 2**ll:
        print("Val over field")
        return
    mask1 = 0x0
    for l in range(ll):
        mask1 |= (1 << (64 - StartBit - l - 1 ))
#     print("mask1: ", hex(mask1))
    mask2 = ~mask1
    print("mask2: ", hex(mask2))
    y = 0
    for i in range(8):
        y = y + (Addr[i] << (56 - 8*i))
    y = y & mask2
    print("y: ", hex(y))
#     cc = len(bin(Val))
#     print("Val len: ", cc) 
#     x = Val <<  (64 - StartBit - cc)
    x = Val <<  (64 - StartBit - ll)
    print("_x: ", hex(x))
    x = x | y
    print("x: ", hex(x))
    
    for i in range(8):
        Addr[i] = 0xff & (x >> (56 - 8*i))
        print("Addr[%d] are: %s" % (i, hex(Addr[i])))
    pass
------------------------------------------------------------
# Signal2Msg(Addr, 0, 32, 2)

# file_List = []
# for root, dirs, files in os.walk('.'):
#     for f in files:
#         if os.path.splitext(f)[1] == '.py':
#             file_List.append(f)
# print(file_List)

-----------------------------------------------------------


prelist = locals()
for i in 1,2,3:
    prelist['list' + str(i)] = i
print(list2)

num = 5

print(locals()['a'][4])
------------------------------------

import threading, time, sys

def func(evt):
    i = 0
    while True:
        print(i)
        evt.wait()
        time.sleep(0.5)
        i += 1
event1 = threading.Event()
event1.clear()
t1 = threading.Thread(target = func, args = (event1,))
t1.start()

while True:
    data = input('pls input event: ')
    if data == '0':
        event1.clear()
    elif data == '1':
        event1.set()
    elif data == 's':
        sys.exit()


x = b'\x10\x02\x65'
data = list(x)
print(type(data[0]))
# d = list(int(x))
# print(type(d))



import can 

msg = can.Message(arbitration_id = 0x105)
msg.data=[1,2,3,4,5,6,7,8]
bus = can.Bus(interface='zlgcan')
bus.send(msg)
bus.recv(1)
bus.shutdown()



b = b'\x01\x02\x03'
print('b:%s'%b)
lb = list(b)
print(lb)
b2 = bytearray(lb)
print(b2)


def String2Bytes(s):
    data = []
    l = len(s)
    if l%2 is not 0:
        print('len should be Oven!')
        return
    try:
        n = 0
        while n < l:
            data.append(int(s[n:n+2],16))
            n += 2
        b = bytes(data)
        return b
    except:
        print('transform error!')
    
b = bytes.fromhex('57414c544f4e532d5745422e434f4d2020')
print(b)

from PyCRC import CRC16
from builtins import int
tmp = CRC16.CRC16()
# print(tmp.crc16_tab)
a = [0x34,0x80,0x0A,0x00,0x00,0x02,0x6C,0x01]
b = [0x34,0x80,0x0A,0x00,0x00,0x02,0x6C,0x01,0x7e,0xc3]
print(hex(tmp.calculate(bytes(a))^0xffff))
print(hex(tmp.calculate(bytes(b))))


from Bootloader.Hex_Parser import HexFile as H
outputhex_name = '../lib/memory.hex'
inputhex_name = '../lib/DM330018_Starter_Kit_Demo.X.production.hex'
Hexo = H.load(outputhex_name)
Hexi = H.load(inputhex_name)

print(Hexo.segments)
print(Hexi.segments)

APP_SIZE_BYTES = 0x4e000

print(Hexo.segments[0].data[0x6800+APP_SIZE_BYTES-6*4:0x6800+APP_SIZE_BYTES])
for i in Hexo.segments[0].data[0x400:0x400+8]:
    print('%x'%i)
# print(Hexi.segments[1].data[0x0:0x0+14004])
'''

from signals import *
from messages import *
from dbc import dbc
from can import Message

def Msg2Signal(M):
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
                    print("candata: %x"%candata)
                    for s in m_t.signals:
                        s.initial_value = (candata >> s.Shift_Bits) % (2**s.bitlength)
                        print(s.name, ': ' , s.initial_value)
            except:
                print("Msg2Signal exception!")

m = Message(arbitration_id = 0xcff00a0, data = [0x0,0x0,0x0,0x0,0x0,0x8,0x0,0x11])
print("M: ",m)
Msg2Signal(m)










    