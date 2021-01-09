# coding: utf-8

"""
This interface is for Windows only, otherwise use socketCAN.
"""

from __future__ import division, print_function, absolute_import

import logging
from ctypes import byref

from can import BusABC, Message, CanError
from .zlgcanabstractionlayer import *
import binascii
from fileinput import filename

# Set up logging

log = logging.getLogger('can.zlgcan')
''' Send Self, loop test      0 normal; 1 single; 2 self '''
CAN_transmit_type = 1

def message_convert_tx(msg):
    message_tx = ZCAN_Transmit_Data()
    message_tx.transmit_type = CAN_transmit_type
    length = msg.dlc
    message_tx.frame.can_dlc = length

    message_tx.frame.can_id = msg.arbitration_id

    for i in range(length):
        message_tx.frame.data[i] = msg.data[i]

    if msg.is_error_frame:
        message_tx.frame.err = 1

    if msg.is_remote_frame:
        message_tx.frame.rtr = 1 #remote frame

    if msg.is_extended_id:
        message_tx.frame.eff = 1

    return message_tx


def message_convert_rx(rx):
    """convert the message from the CANAL type to pythoncan type"""
    message_rx = rx[0]
    is_extended_id = message_rx.frame.eff
    is_remote_frame = message_rx.frame.rtr
    is_error_frame = message_rx.frame.err

    return Message(timestamp=message_rx.timestamp,
                   is_remote_frame=is_remote_frame,
                   is_extended_id=is_extended_id,
                   is_error_frame=is_error_frame,
                   arbitration_id=message_rx.frame.can_id,
                   dlc=message_rx.frame.can_dlc,
                   data=message_rx.frame.data[:message_rx.frame.can_dlc])


class ZlgcanBus(BusABC):
    """Interface to a USB2CAN Bus.

    This interface only works on Windows.
    Please use socketcan on Linux.

    :param str channel (optional):
        The device's serial number. If not provided, Windows Management Instrumentation
        will be used to identify the first such device.

    :param int bitrate (optional):
        Bitrate of channel in bit/s. Values will be limited to a maximum of 1000 Kb/s.
        Default is 500 Kbs

    :param int flags (optional):
        Flags to directly pass to open function of the usb2can abstraction layer.

    :param str dll (optional):
        Path to the DLL with the CANAL API to load
        Defaults to 'usb2can.dll'

    :param str serial (optional):
        Alias for `channel` that is provided for legacy reasons.
        If both `serial` and `channel` are set, `serial` will be used and
        channel will be ignored.

    """

    def __init__(self, device_type=ZCAN_USBCANFD_200U, channel=0, bitrate=500000, *args, **kwargs):

        self.can = ZlgCanAbstractionLayer()

        # convert to kb/s and cap: max rate is 1000 kb/s
        baudrate = min(int(bitrate // 1000), 1000)
        
        self.handle = self.can.OpenDevice(device_type, 0,0)
        if self.handle == INVALID_DEVICE_HANDLE:
            log.error("Open Device failed!")
            ex = Exception('OpenDeviceFailed')
            raise ex
#             exit(0)
            return
        log.info("device handle:%d." %(self.handle))
        
#         info = self.can.GetDeviceInf(self.handle)
#         log.info("Device Information:\n%s" %(info))

        #Start CAN
        #Initial channel
        if True: #resistance enable
            ip = self.can.GetIProperty(self.handle)
            #Conf Terminator
            ret = self.can.SetValue(ip, 
                                str(channel) + "/initenal_resistance", 
                                '1')
            if ret != ZCAN_STATUS_OK:
                log.error("Open CH%d resistance failed!" %(channel))
            #Conf CANFD Clock
            ret = self.can.SetValue(ip, str(channel) + "/clock", "60000000")
            if ret != ZCAN_STATUS_OK:
                log.error("Set CH%d CANFD clock failed!" %(channel))
            self.can.ReleaseIProperty(ip)
            
        chn_cfg = ZCAN_CHANNEL_INIT_CONFIG()
        chn_cfg.can_type = ZCAN_TYPE_CANFD

        chn_cfg.config.can.mode = 0
        if bitrate == 500000:
            chn_cfg.config.canfd.abit_timing = 104286  #500k Baudrate
            chn_cfg.config.canfd.dbit_timing = 104286

        self.chn_handle = self.can.InitCAN(self.handle, channel, chn_cfg)
        if self.chn_handle == INVALID_CHANNEL_HANDLE:
            log.error("OpenCANChannel: Init CAN fail!")
            return 
            
        ret = self.can.StartCAN(self.chn_handle)
        if ret != ZCAN_STATUS_OK: 
            log.error("OpenCANChannel: Start CAN fail!")
            return 
        log.info("channel handle:%d." %(self.chn_handle))

        super(ZlgcanBus, self).__init__(channel=channel, bitrate=bitrate, *args, **kwargs)

    def send(self, msg, timeout=None):
        tx = message_convert_tx(msg)

        status = self.can.Transmit(self.chn_handle, tx, 1)
        log.debug('Send: id:%x , data:[%s]'%(msg.arbitration_id, binascii.hexlify(msg.data)))

        if status != 1:
            raise CanError("could not send message: status == {}".format(status))


    def _recv_internal(self, timeout):

        rcv_num = self.can.GetReceiveNum(self.chn_handle, ZCAN_TYPE_CAN)
        if rcv_num:
            if timeout == 0 or timeout is None:
                rcv_msg, rcv_num = self.can.Receive(self.chn_handle, 1)
    
            else:
                time = int(timeout * 1000)
                rcv_msg, rcv_num = self.can.Receive(self.chn_handle, 1, time)

        if rcv_num == 1:
            rx = message_convert_rx(rcv_msg)
            log.debug('Recv: id:%x , data:[%s]'%(rx.arbitration_id, binascii.hexlify(rx.data)))
        else:
#             log.debug('Canal Error %s', str(rcv_num))
            rx = None

        return rx, False

    def shutdown(self):
        """
        Shuts down connection to the device safely.

        :raise cam.CanError: is closing the connection did not work
        """
        if self.chn_handle:
            self.can.ClearBuffer(self.chn_handle) # added in 20200107 by dongdong
            self.can.ResetCAN(self.chn_handle)
        if self.handle:
            self.can.CloseDevice(self.handle)


