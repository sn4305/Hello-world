from canlib import canlib


def dumpMessage(id, msg, dlc, flag, time):
    """Prints a message to screen"""
    if (flag & canlib.canMSG_ERROR_FRAME != 0):
        print("***ERROR FRAME RECEIVED***")
    else:
        dataStr = ""
        for i in range(0, 8):
            if(i < len(msg)):
                dataStr += "{0:3} ".format(msg[i])
            else:
                dataStr += "    "
        print("{0:0>8b}  {1}   {2}   {3}".format(id, dlc, dataStr, time))


def dumpMessageLoop(ch):
    """Listens for messages on the channel and prints any received messages"""
    finished = False
    print("   ID    DLC DATA                                Timestamp")
    while not finished:
        try:
            id, msg, dlc, flag, time = ch.read(50)
            hasMessage = True
            while hasMessage:
                dumpMessage(id, msg, dlc, flag, time)
                try:
                    id, msg, dlc, flag, time = ch.read()
                except(canlib.canNoMsg) as ex:
                    hasMessage = False
                except (canlib.canError) as ex:
                    print(ex)
                    finished = True
        except(canlib.canNoMsg) as ex:
            None
        except (canlib.canError) as ex:
            print(ex)
            finished = True


if __name__ == '__main__':
    # Initialization
    num_channels = canlib.getNumberOfChannels()
    print("Found %d channels" % num_channels)
    for ch in range(0, num_channels):
        chdata = canlib.ChannelData(ch)
        print("%d. %s (%s / %s)" % (ch, chdata.channel_name,
                                chdata.card_upc_no,
                                chdata.card_serial_no))
                                
    channel = 0
    # ch = canlib.openChannel(channel, canlib.canOPEN_ACCEPT_VIRTUAL)
    ch = canlib.openChannel(channel)
    ch.setBusParams(canlib.canBITRATE_250K)
    ch.busOn()

    # Start listening for messages
    dumpMessageLoop(ch)

    # Channel teardown
    ch.busOff()
    ch.close()
