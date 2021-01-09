#
# Class to hold all properties of a CAN signal
# as it is represented in a DBC file
#

class SignalValueType:
    UNSIGNED = "+"
    SIGNED = "-"
    FLOAT = "SIG_VALTYPE_ 1"
    DOUBLE = "SIG_VALTYPE_ 2"

class SignalByteOrder:
    INTEL = "1"
    MOTOROLA = "0"

class Signal:
    #
    # Initialize object
    #
    def __init__(self, s=None, debug=False):
        self.val = None  #real value
        if s is None:
            self.clear()
        else:
            self.parse(s, debug)

    #
    # Create and clear all signal properties
    #
    def clear(self):
        self.name = ""
        self.valuetype = SignalValueType.UNSIGNED
        self.startbit = 0
        self.bitlength = 0
        self.byteorder = SignalByteOrder.MOTOROLA
        self.minimum = 0
        self.maximum = 0
        self.factor = 1
        self.offset = 0
        self.initial_value = 0
        self.unit = ""
        self.Byte_MSB_Col = 0
        self.Byte_MSB_Row = 0
        self.Byte_LSB_Col = 0
        self.Byte_LSB_Row = 0
        self.Shift_Bits = 0
    #
    # Parse signal from line string
    #
    def parse(self, s, debug=False):
        self.clear()
        parts = s.split(" ")
        if parts[0] != "" or parts[1] != "SG_":
            print("Aborting: Expected \"SG_\" at the beginning of signal. Got \"" + parts[1] + "\".")
            return
        self.name = parts[2]
        layout = parts[4]    # 36|12@1+
        p = layout.split("|")
        self.startbit = int(p[0])
        q = p[1].split("@")
        self.bitlength = int(q[0])
        self.byteorder = q[1][0]   #1: intel, 2:Motorola
        self.valuetype = q[1][1]   #+: unsigned, -: signed
        factor_offset = parts[5]    # (1,0)
        p = factor_offset.split(",")
#         self.factor = int(p[0][1:])
        self.factor = float(p[0][1:])
        self.offset = int(p[1][:-1])
        min_max = parts[6]    # [0|255]
        p = min_max.split("|")
        self.minimum = float(p[0][1:])
        self.maximum = float(p[1][:-1])
        self.unit = parts[7][1:-1]    # in quotes

        self.Byte_MSB_Col = self.startbit % 8
        self.Byte_MSB_Row = self.startbit // 8
        if self.bitlength <= self.Byte_MSB_Col + 1:
            #Single row - test OK
            self.Byte_LSB_Col = self.Byte_MSB_Col + 1 - self.bitlength
            self.Byte_LSB_Row = self.Byte_MSB_Row
        else:
            #Multi rows
            self.Byte_LSB_Row = self.Byte_MSB_Row + 1 + (self.bitlength - self.Byte_MSB_Col - 2) // 8
            self.Byte_LSB_Col = (self.Byte_LSB_Row - self.Byte_MSB_Row + 2)*8 - self.Byte_MSB_Col - self.bitlength - 1
        # print("Byte_MSB_Row: %d, Byte_MSB_Col: %d"%(Byte_MSB_Row,Byte_MSB_Col))
        # print("Byte_LSB_Row: %d, Byte_LSB_Col: %d"%(Byte_LSB_Row,Byte_LSB_Col))
        self.Shift_Bits = 64 - ((1+self.Byte_LSB_Row)*8 - self.Byte_LSB_Col)
    #
    # Export signal as string for DBC file
    #
    def __str__(self):
        layout = str(self.startbit) + "|" + str(self.bitlength) + "@" + self.byteorder + self.valuetype
        factor_offset = "(" + str(self.factor) + "," + str(self.offset) + ")"
        min_max = "[" + str(self.minimum) + "|" + str(self.maximum) + "]"
        line = " SG_ " + self.name + " : " + layout + " " + factor_offset + " " + min_max + " \"" + self.unit + "\" Vector__XXX\n"
        return line
