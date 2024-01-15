import ctypes
import json
import os
import select

if os.path.isfile("config.json"):
    json_file = open('config.json','r')
    config_json = json_file.read()
    data = json.loads(config_json)
    devGrp = data["group"]
else: 
    config_json = '{"devices":[], "group":[]}'
    data = json.loads(config_json)
    x = 0
    while x < 16:
        data["group"].append({str(x):[{"Device":99}]})
        devGrp = data["group"]
        x +=1
def writeToConfJson():
    with open("config.json", "w") as json_file:
        json.dump(data, json_file)

def send_command(file_in, command):
   global x
   seq = str(f"{x:02x}") + command
   file_in.write(seq.encode('utf-8'))
   x += 1
   if x == 255:
      x = 0
def init():
    send_command(file_in, "2000")
    libc.usleep(90000)
    send_command(file_in, "2000")
    libc.usleep(90000)
    send_command(file_in, "A500")
    libc.usleep(90000)
    send_command(file_in, "A500")
    libc.usleep(90000)
    if not os.path.isfile("config.json"):
        send_command(file_in, "A700")
        libc.usleep(90000)
        send_command(file_in, "A700")
        libc.usleep(90000)

def SearchAndCompare(fd, addr):

    h = addr >> 16
    h = h & 0xff

    m = addr >> 8
    m = m & 0xff

    l = addr & 0xff

    send_command(fd, "B1" + f'{h:02x}')
    libc.usleep(34194)

    send_command(fd, "B3" +f'{m:02x}')
    libc.usleep(34194)

    send_command(fd, "B5" + f'{l:02x}')
    libc.usleep(34194)

    send_command(fd, "A900")
    libc.usleep(34194)

    rfds, wfds, efds = select.select( [file_in], [], [], 1)
    if rfds:
        rfds[0].readline()
        # print(rfds[0].readline())
        return 1
    else:
        # print('none')
        return 0

libc = ctypes.CDLL('libc.so.6')
file_in = open('/dev/dali','wb+', buffering=0)
x = 0

init()
ShortAddrArray = [False] * 64
if os.path.isfile("config.json"):
        for device in data["devices"]:
            ShortAddrArray[device["Short"]] = True
ShortAddr = 0
while ShortAddr < 64:
    while ShortAddrArray[ShortAddr]:
        ShortAddr += 1       
    # print("ShortAddr: ", ShortAddr)
    SearchAddr = 0xFFFFFF
    LowLimit = 0
    HighLimit = 0x1000000
    # print("search address ", hex(SearchAddr))
    Response = SearchAndCompare(file_in, SearchAddr)
    if Response == 1:
        print("Device detected, address searching...\n")
        if SearchAndCompare(file_in, SearchAddr - 1) == 0:
            SearchAndCompare(file_in, SearchAddr)
            if not os.path.isfile("config.json"):
                print("24-bit address found ", hex(SearchAddr) , "- assigning short address " , ShortAddr)
                print("resp = 1 no cfg found...")
                data["devices"].append({"Address":f'{SearchAddr:02x}', "Short":ShortAddr})
                setAddr = ((ShortAddr << 1) | 1)
                send_command(file_in, "B7" + f'{setAddr:02x}')
                libc.usleep(102582)
                send_command(file_in, "AB00")
                libc.usleep(34194)
            else:
                isSet = False
                for device in data["devices"]:
                    if f'{SearchAddr:02x}' == device["Address"]:
                        print("24-bit address found first ", hex(SearchAddr), "- assigning short address ", device["Short"])
                        print("resp = 1 found...")
                        setAddr = ((device["Short"] << 1) | 1)
                        send_command(file_in, "B7" + f'{setAddr:02x}')
                        libc.usleep(102582)
                        send_command(file_in, "AB00")
                        libc.usleep(34194)
                        isSet = True
                if not isSet:
                    data["devices"].append({"Address":f'{SearchAddr:02x}', "Short":ShortAddr})
                    setAddr = ((ShortAddr << 1) | 1)
                    send_command(file_in, "B7" + f'{setAddr:02x}')
                    libc.usleep(102582)
                    send_command(file_in, "AB00")
                    libc.usleep(34194)
                    print("24-bit address found first ", hex(SearchAddr) , "- assigning short address " , ShortAddr)
                    print("resp = 1 not found...")
            break
    else:
        print("No devices detected\n")
        break
    while 1:
        SearchAddr = int((LowLimit + HighLimit) / 2)
        Response = SearchAndCompare(file_in, SearchAddr)
        if Response == 1:
                if SearchAddr == 0 or SearchAndCompare(file_in, SearchAddr - 1) == 0:
                    break
                HighLimit = SearchAddr
        else:
            LowLimit = SearchAddr
    SearchAndCompare(file_in, SearchAddr)
    if not os.path.isfile("config.json"):
                data["devices"].append({"Address":f'{SearchAddr:02x}', "Short":ShortAddr})
                print("24-bit address found first ", f'{SearchAddr:02x}', "- assigning short address ", ShortAddr)
                print("No cfg found...")
                setAddr = ((ShortAddr << 1) | 1)
                send_command(file_in, "B7" + f'{setAddr:02x}')
                libc.usleep(102582)
                send_command(file_in, "AB00")
                libc.usleep(34194)
    else:
        found = False
        for device in data["devices"]:
            if f'{SearchAddr:02x}' == device["Address"]:
                print("24-bit address found first ", hex(SearchAddr), "- assigning short address ", device["Short"])
                print("Found...")
                setAddr = ((device["Short"] << 1) | 1)
                send_command(file_in, "B7" + f'{setAddr:02x}')
                libc.usleep(102582)
                send_command(file_in, "AB00")
                libc.usleep(34194)
                found = True
        if not found:
            data["devices"].append({"Address":f'{SearchAddr:02x}', "Short":ShortAddr})
            print("24-bit address found first ", f'{SearchAddr:02x}', "- assigning short address ", ShortAddr)
            print("Not found...")
            setAddr = ((ShortAddr << 1) | 1)
            send_command(file_in, "B7" + f'{setAddr:02x}')
            libc.usleep(102582)
            send_command(file_in, "AB00")
            libc.usleep(34194)
    ShortAddr += 1
GroupCnt = 0
for group in devGrp:
    devList = group[str(GroupCnt)]
    for dev in devList:
        if not dev['Device'] == 99:
            print("Adding device ", dev['Device'], " to group ", GroupCnt)
            devID = int(dev['Device'])
            # print(f'{devID:0>{6}b}')
            string = "0" + f'{devID:0>{6}b}' + "10110" + f'{GroupCnt:0>{4}b}'
            hexval = '{:0{width}x}'.format(int(string,2), width=4)
            # print(hexval)
            send_command(file_in, hexval)
            libc.usleep(90000)
            send_command(file_in, hexval)
            libc.usleep(90000)
    GroupCnt += 1
writeToConfJson()
send_command(file_in, "A100")
print("Exiting...")
file_in.close()