#
# Data base CAN (DBC) file format library
#
# A DBC file contains information about the
# constitution of CAN messages (frames) and
# the signals they are consituted from.
# This library supports reading DBC files
# and writing matching C structs
# e.g. for implementation on a microcontroller.
#

from messages import Message
from datetime import datetime
import os
dbc = []


class DBC:
    #
    # Initialize object
    #
    def __init__(self, s=None, debug=False):
        if s is None:
            self.clear()
        else:
            self.parse(s, debug=debug)

    #
    # Create and clear all object properties
    #
    def clear(self):
        self.version = "";
        self.namespace = [];
        self.messages = [];

    #
    # Import object from DBC file
    #
    def load(self, filename, debug=False):
        self.parse(open(filename, "r").read(), debug=debug)

    #
    # Parse object properties from string
    #
    def parse(self, s, debug=False):
        self.clear()
        lines = s.split("\n")

        if debug:
            print(lines)

        PARSE_TOP = 0
        PARSE_NS = "NS_ : "
        PARSE_BS = "BS_:"
        PARSE_BU = "BU_:"
        PARSE_BO = "BO_ "
        PARSE_CM = "CM_ "

        state = PARSE_TOP

        for line in lines:
            line = line.replace("\t", " ")
            if state == PARSE_TOP:
                # skip empty lines
                if line.strip() == "":
                    continue
                parts = line.split(" ")
                if len(parts) < 1:
                    continue
                # DBC file version
                if parts[0] == "VERSION":
                    if debug:
                        print("Parsing version...")
                    self.version = parts[1][1:-1]    # without the quotes
                    continue
                # begin sub-block
                buffer = ""
                if line[:4] in [PARSE_NS, PARSE_BS, PARSE_BU]:
                    state = line[:4]
                    if debug:
                        print("Parsing " + str(state) + "...")
                elif len(line) > 3 and line[:4] == PARSE_BO:
                    state = PARSE_BO
                    if debug:
                        print("Parsing " + str(state) + "...")
                elif len(line) > 3 and line[:4] == PARSE_CM:
                    state = PARSE_CM
                    if debug:
                        print("Parsing " + str(state) + "...")
                else:
                    if debug:
                        print("Warning: Unrecognized statement: " + line)

            if state == PARSE_NS:
                # empty line: return to top
                if line.strip() == "":
                    state = PARSE_TOP
                    if debug:
                        print("Return to top")
                    continue
                self.namespace.append(line.strip())

            if state == PARSE_BO:
                # empty line: parse buffer and return to top
                if line.strip() == "":
                    self.messages.append(Message(buffer))
                    state = PARSE_TOP
                    if debug:
                        print("buffer: " + buffer)
                        print("Return to top")
                    continue
                buffer += line + "\n"
                
            if state == PARSE_CM:
                # empty line: parse buffer and return to top
                if line.strip() == "":
                    state = PARSE_TOP
                    continue
                parts = line.split(" ")
                if line[4:8] == PARSE_BO:
                    for msg in self.messages:
                        if msg.ID == int(parts[2]):
#                             print("msg.ID: ", msg.ID)
#                             print("parts[3][1:2]--- ", parts[3][1:2])
#                             print("parts[4][0:1]--- ", parts[4][0:1])
                            if 'MB' == parts[3][1:3]:
                                msg.MailBox = int(parts[3][4:])
#                                 print("msg.MailBox: ", msg.MailBox)
                            if 'TO' == parts[4][0:2]:
                                msg.canlostTimeout = int(parts[4][3:-2])
#                                 print("msg.canlostTimeout: ", msg.canlostTimeout)

            # in any case: return to top on an empty line
            if line.strip() == "":
                state = PARSE_TOP
                if debug:
                    print("Return to top")
                continue

    #
    # Export DBC file as string
    #
    def __str__(self):
        version = "VERSION \"" + self.version + "\"\n"

        namespace = "NS_ : \n"
        for ns in self.namespace:
            namespace += "\t" + ns + "\n"

        messages = ""
        for message in self.messages:
            messages += str(message) + "\n"

        buffer = version + "\n" + namespace + "\n" + "BS_:\n\nBU_:\n\n" + messages
        return buffer
    
''' set up dbc lib'''
file_List = []
file_List1 = []
idx = 0
for root, dirs, files in os.walk('../lib'):
    for f in files:
        if os.path.splitext(f)[1] == '.dbc':
            file_List.append(os.path.join(root,f))
            file_List1.append(os.path.splitext(f)[0])
            dbc.append(DBC())
            dbc[idx].load(os.path.join(root,f))
#             dbcname = locals()
#             dbcname[file_List1[idx]] = DBC()
#             dbcname[file_List1[idx]].load(os.path.join(root,f))
            idx += 1
# print(file_List1)

    
    

if __name__ == "__main__":
    ff = 0
    j = 0
    for _dbc_ in dbc:
        i = 0
        try:
            #open(file_List1[j] +'.c','w') as f, open(file_List1[j] +'.h','w') as h,
            with open(file_List1[j] +'.py','w') as p:
                print('from dbc import dbc\n' , file = p)
                '''
                print("/*    This file is generated by dbc.py, Do not modify it. \n**\n**\
        Modified Date + Time: %s \n**\n**\
        Parsed dbc file name: %s */\n\n" %( datetime.now(), file_List[j]), file = f)
                print('#include "%s.h"\n' % file_List1[j], file = f)
                
                
                print("/*    This file is generated by dbc.py, Do not modify it. \n**\n**\
        Modified Date + Time: %s \n**\n**\
        Parsed dbc file name: %s */\n\n" %( datetime.now(), file_List[j]), file = h)
                print('#ifndef %s_H' % file_List1[j] , file = h)
                print('#define %s_H\n\n' % file_List1[j], file = h)
                print('#include "DBC_Type.h"\n', file = h)
                '''
                for message in _dbc_.messages:
            #         print("typedef struct{")
            #         print("    u32 MSG_ID;")
            #         print("    u8 MSG_LEN;")
                    # print("static SIGNAL Signal%d[%d] = {" %(i,len(message.signals)), file = f)
                    SIG_NAME_IDX = 0
                    for sig in message.signals:
                        '''
                        print("    {", file = f)
                        print('        .name = \"%s\",' % sig.name, file = f)
                        print("        .startbit = %d," % sig.startbit, file = f)
                        print("        .bitlength = %d," % sig.bitlength, file = f)
                        print("        .raw_value = %d," % sig.initial_value, file = f)
                        print("        .minimum = %d," % sig.minimum, file = f)
                        print("        .maximum = %d," % sig.maximum, file = f)
                        print("        .factor = %.2f," % sig.factor, file = f)
                        print("        .offset = %.1f," % sig.offset, file = f)
                        print("        .initial_value = %.1f," % sig.initial_value, file = f)
                        print("    },", file = f)
                        '''
                        #add signal name #define
                        # print("#define    %-40s    %s.pMessage[%d].pSignal[%d]" 
                        #       % ('ID_' + str(hex(message.ID)) + '__' + sig.name, file_List1[j], i, SIG_NAME_IDX), 
                        #       file = h)
                        print("%-40s    =    dbc[%d].messages[%d].signals[%d]" 
                              % ('ID_' + str(hex(message.ID)) + '__' + sig.name, ff, i, SIG_NAME_IDX), 
                              file = p)
                        SIG_NAME_IDX += 1
                                            
                    # print("};", file = f)
                    # print("", file = f)
                    i += 1
                    
                i = 0
                '''
                print("static MESSAGE Message[%d] = {" % len(_dbc_.messages), file = f)
                             
                for message in _dbc_.messages:
                    
                    print("    {", file = f)
                    print("        .msg = {0, 0x%x, {0}, %d}," % (message.ID, message.DLC), file = f)
                    print('        .MailBox = %d,' % message.MailBox, file = f)
                    print('        .canlostCounter  = 0,' , file = f)
                    print('        .canlostTimeout = %d,' % message.canlostTimeout, file = f)
                    print('        .sender = %s,' % message.sender, file = f)
                    print("        .pSignal = Signal%d," % i, file = f)
                    print("        .numSig = %d," % len(message.signals), file = f)
                    print("    },", file = f)
                    print("", file = f)
                    
#                     sig_id = 0
#                     # 
#                     for sig in message.signals:
#                         print("    %s.pMessage[%d].pSignal[%d]," %(file_List1[j], i, sig_id)  , file = h)
#                         sig_id += 1
                              
                    i += 1
                        
                print("};", file = f)
                
                print("DBC %s = {" % file_List1[j], file = f)
                print("\nextern DBC %s;\n\n" % file_List1[j] , file = h)
                print("    .pMessage = Message,", file = f)
                print("    .numMsg = %d," % len(_dbc_.messages), file = f)
                print("};\n\n", file = f)
                print("/*  file end  */", file = f)
                
                print("#endif  \n\n", file = h)
                print("/*  file end  */", file = h)
                j = j + 1 
                '''
        except:
            print("open file error!")
            
        ff += 1
        
            
#     print(dbc)