# pip install pymssql
import sys
import array
import threading
import time
from datetime import datetime
import pymssql
import socket
import json
from threading import Thread
import os.path
from os import path
import fins.udp
import numbers
import ast
import copy
# import win_inet_pton
from pyModbusTCP.client import ModbusClient
from ping3 import ping, verbose_ping
from PyUtility import utility_network
from FX5 import FX5

sys.path.append(os.path.abspath(os.path.dirname('D:\FactoryCommPY\API_Backbone\PyUtility.py')))  # เพิ่ม path ของไฟล์ปัจจุบัน

port = 20001
hostname = socket.gethostname()
hostaddr = socket.gethostbyname(hostname)
#use for ping server
ip_group = []
ping_package = {"addr":0,"value":0,"scantime":0,"except":""}

def SendbackToClientAndCloseConnection(client, data):
    package = json.dumps(data)
    sendback = "HTTP/1.1 200 OK\r\n"
    sendback += " Access-Control-Allow-Headers: *\r\n"
    sendback += "Access-Control-Allow-Origin: *\r\n"
    sendback += "Connection: keep-alive\r\n"
    sendback += "Server: " + hostname + "\r\n"
    sendback += "Content-Type: application/json\r\n"
    sendback += "Content-Length: " + str(len(package)) + "\r\n"
    sendback += "\r\n"
    sendback += package
    client.sendall(sendback.encode())
    client.close()
    return 0
def SendbackHtmlToClientAndCloseConnection(client, data):
    package = data
    sendback = "HTTP/1.1 200 OK\r\n"
    sendback += "Access-Control-Allow-Origin: *\r\n"
    sendback += "Connection: close\r\n"
    sendback += "Server: " + hostname + "\r\n"
    sendback += "Content-Type: text/html\r\n"
    sendback += "Content-Length: " + str(len(package)) + "\r\n"
    sendback += "\r\n"
    sendback += package
    client.sendall(sendback.encode())
    client.close()
    return 0
# microservice fins_udp
class omron_fins_udp:
    # Package Example
    # {
    #    "service": "omron_fins_udp",
    #    "connection": {"source":"192.168.1.1","port":502},
    #    "command": [
    #                  {"access":"r","addr":"D20000","size":10,"value":[0,1,2,3,4,5,6,7,8,9],"except":""},
    #                  {"access":"w","addr":"CIO100","size":10,"value":[],"except":""},
    #                  {"access":"r","addr":"D0","size":10,"value":[],"except":""},
    #                  {"access":"w","addr":"D1000","size":10,"value":[0,1,2,0,23,434,123,343,454,343,343,3434],"except":""}
    #                ]
    #    "response": [{"access":"read","addr":"400001","value":0}],
    #    "ready": True,
    #    "exception": ""
    # }
    def __init__(self,event):
        event["ready"] = True
        try:
            for self.transaction in event["command"]:
                try:
                        # Page7 https://www.myomron.com/downloads/1.Manuals/Networks/W227E12_FINS_Commands_Reference_Manual.pdf
                        self.response = {"ICF":0,"RSV": 0, "GCT": 0, "DNA": 0, "DA1": 0, "DA2": 0, "SNA": 0, "SA1": 0, "SA2": 0,"SID": 0, "COMMANDCODE": 0, "RESPONSE": 0};
                        self.driver = fins.udp.UDPFinsConnection()
                        self.driver.connect(event["connection"]["source"],int(event["connection"]["port"]))
                        self.driver.dest_node_add =1 #int(event["connection"]["source"].split(".")[3])
                        self.driver.srce_node_add =25 #int(hostaddr.split(".")[3])
                        #select plc area
                        if(self.transaction["addr"].find("D") == 0):
                            self.plcarea = fins.FinsPLCMemoryAreas().DATA_MEMORY_WORD
                            self.plcaddress =  int(self.transaction["addr"][1:])
                        elif(self.transaction["addr"].find("CIO") == 0):
                            self.plcarea = fins.FinsPLCMemoryAreas().CIO_WORD
                            self.plcaddress = int(self.transaction["addr"][3:])
                        #select read/write
                        self.res = ""
                        if self.transaction["access"] == "r":
                           self.res = self.driver.memory_area_read(self.plcarea,(self.plcaddress<<8).to_bytes(3,'big'),int(self.transaction["size"]))
                        #check writemode and size write match with value length
                        elif ((self.transaction["access"] == "w") and (int(self.transaction["size"]) == int(len(self.transaction["value"])) )):
                            #{"access": "w", "addr": "D1000", "size": 10,"value": [0, 1, 2, 0, 23, 434, 123, 343, 454, 343, 343, 3434], "except": ""}
                            self.datawrite = []
                            for self.dataout in self.transaction["value"] :
                                    self.HB = int(self.dataout)>>8 & 0xFF
                                    self.LB = int(self.dataout) & 0xFF
                                    self.datawrite.append(self.HB)
                                    self.datawrite.append(self.LB)
                            self.datawrite_byte = bytearray(self.datawrite)
                            self.res = self.driver.memory_area_write(self.plcarea,(self.plcaddress<<8).to_bytes(3,'big'),self.datawrite_byte,int(self.transaction["size"]))
                            self.complete=0

                        # check package recive
                        if len(self.res) >= 14 :
                            self.response["ICF"] = self.res[0]
                            self.response["RSV"] = self.res[1]
                            self.response["GCT"] = self.res[2]
                            self.response["DNA"] = self.res[3]
                            self.response["DA1"] = self.res[4]
                            self.response["DA2"] = self.res[5]
                            self.response["SNA"] = self.res[6]
                            self.response["SA1"] = self.res[7]
                            self.response["SA2"] = self.res[8]
                            self.response["SID"] = self.res[9]
                            self.response["COMMANDCODE"] = self.res[10] << 8 | self.res[11]
                            self.response["RESPONSE"] = self.res[12] << 8 | self.res[13]
                            # pack data send to client
                            if (self.transaction["access"] == "r") :#and self.response["RESPONSE"] == 0 :
                                        self.sendback = []
                                        for self.index in range(int(self.transaction["size"])):
                                           data = int(self.res[14+2*self.index]<<8 | self.res[14+2*self.index+1])
                                           self.sendback.append(data)
                                           self.transaction["value"] = self.sendback
                            elif self.transaction["access"] == "w" : #and self.response["RESPONSE"] == 0 :
                                self.dummy = 0
                            else:
                                self.transaction["except"] = "response fail 1"
                                event["ready"] = False
                        else:
                            self.transaction["except"] = "response fail 2"
                            event["ready"] = False
                except Exception as e:
                    self.transaction["except"] = str(e)
                    event["ready"] = False
        except Exception as e :
            event["exception"] = str(e)
            event["ready"] = False
# microservice fx5u slmp
class mitsubishi_slmp_tcp:
    def __init__(self,event):
        event["ready"] = True
        self.ip = event["connection"]["source"]
        self.port = str(event["connection"]["port"])
        try:
            for self.transaction in event["command"]:
                try:
                        # github https://github.com/UTAIOT-team/mitsubishi-fx5/blob/try-oee_with_schedule/fx5.py
                        if self.transaction["access"] == "r":
                            self.mem = {"addr":int(self.transaction["addr"][1:]),"size":self.transaction["size"]}
                            self.driver = FX5(self.ip + ":" + self.port)
                            self.driver.get_connection(self.ip + ":" + self.port)
                            self.sendback = []
                            for x in range(self.mem["size"]):
                                self.addr = "D" + str(self.mem["addr"] + x)
                                self.result = self.driver.read(self.addr)
                                self.sendback.append(self.result)
                            self.transaction["value"] = self.sendback
                            print(self.transaction["value"])
                            self.driver.close_all()
                            
                        #check writemode and size write match with value length
                        elif ((self.transaction["access"] == "w") and (int(self.transaction["size"]) == int(len(self.transaction["value"])) )):
                            #{"access": "w", "addr": "D1000", "size": 10,"value": [0, 1, 2, 0, 23, 434, 123, 343, 454, 343, 343, 3434], "except": ""}
                            self.mem = {"addr":int(self.transaction["addr"][1:]),"size":self.transaction["size"]}
                            self.driver = FX5(self.ip + ":" + self.port)
                            self.driver.get_connection(self.ip + ":" + self.port)
                            for x in range(self.mem["size"]):
                                self.addr = "D" + str(self.mem["addr"] + x)
                                self.value = self.transaction["value"][x]
                                print("cmd " + self.addr + " write " + str(self.value))
                                self.driver.write(self.addr,self.value)
                            self.driver.close_all()
                              
                except Exception as e:
                    self.transaction["except"] = str(e)
                    event["ready"] = False
        except Exception as e :
            event["exception"] = str(e)
            event["ready"] = False
# microservice ping
class os_ping:
    # Package Example
    # {
    #    "service": "ping",
    #    "connection":"",
    #    "command": [
    #                  {"addr":"192.168.1.1","value":0,"except":""},
    #                  {"addr":"192.168.1.2","value":0,"except":""},
    #                  {"addr":"192.168.1.3","value":0,"except":""},
    #                  {"addr":"192.168.1.4","value":0,"except":""},
    #                ]
    #    "response": {"ok":0,"ng":0},
    #    "ready": True,
    #    "exception": ""
    # }
    def __init__(self, event):
            event["ready"] = True
            self.summary = {'ok':0,'ng':0}
            try:
                for self.transaction in event["command"]:
                    try:
                        #check ip match in server ping
                        self.notfoundIP = True
                        for self.target in ip_group :
                          if self.transaction["addr"] == self.target["addr"]:
                              self.notfoundIP = False

                        #fill ip ping in server
                        if self.notfoundIP == True :
                              ip_group.append({"addr":self.transaction["addr"],"value":False,"scantime":0,"except":""})

                        #find ip in server ping
                        for self.target in ip_group :
                              if self.transaction["addr"] == self.target["addr"] :
                                    self.transaction["value"]= self.target["value"]
                                    self.transaction["scantime"] = self.target["scantime"]
                                    if self.transaction["value"] == True :
                                        self.summary["ok"] = self.summary["ok"] + 1
                                    else:
                                        self.summary["ng"] = self.summary["ng"] + 1
                    except Exception as e:
                        self.transaction["except"] = str(e)
                        event["ready"] = False
                event["response"] = self.summary
            except Exception as e :
                event["ready"] = False
                event["exception"] = str(e)
def server_ping():
                print("server ping : started\r")
                while True:
                    for target in ip_group:
                        try:
                            res = ping(target["addr"])
                            print("Ping IP : " + target["addr"] + " -> " + str(res) + " s.")
                            # False None
                            if (((str(res) == "False") or (str(res) == "None")) == False):
                                target["value"] = True
                                target["scantime"] = res
                            else:
                                target["value"] = False
                                target["scantime"] = -1
                        except Exception as e:
                            print("server ping : error " + str(e))
                    time.sleep(1)
# microservice Httpfunction
class HttpPackage:
    def __init__(self, data):
        self.data = bytearray(data).decode('utf-8')
        self.content = self.data.split("\r\n")
        self.test = 0
    def getvalue(self, header):
        for x in self.content:
            self.subheader = x.split(":")
            if self.subheader[0].find(header) >= 0:
                return self.subheader[1]
        return ""
    def get(self):
        self.req = self.content[0].split(" ")[1].lstrip("/")
        return self.req
    def getdata(self):
        self.body = self.data.split("\r\n\r\n")
        return self.body[1]
    def geturl(self):
        self.subdata = self.content[0].split(" ")
        self.body = self.data.split("\r\n\r\n")
        return self.subdata[0],self.subdata[1],self.body[1]
# microservice mssql
class mssql:
    def __init__(self, event):
        try:
            self.sever = event['connection']['source']
            self.user = event['connection']['user']
            self.password = event['connection']['pass']
            self.database = event['connection']['db']
            self.conn = pymssql.connect(self.sever, self.user, self.password, self.database)
            self.cursor = self.conn.cursor()
            self.cursor.execute(event['command'])
            if event['command'][0:6] == "INSERT":
                self.conn.commit()
            elif event['command'][0:6] == "UPDATE":
                self.conn.commit()
            elif event['command'][0:6] == "DELETE":
                self.conn.commit()
            elif event['command'][0:6] == "SELECT":
                self.datarow = self.cursor.fetchone()
                self.datapack = []
                while self.datarow:
                    self.thisRow = []
                    for self.col in range(len(self.datarow)):
                        self.thisRow.append(str(self.datarow[self.col]))
                    self.datapack.append(self.thisRow)
                    self.datarow = self.cursor.fetchone()
                event['response'] = json.dumps(self.datapack)
            else:
                self.conn.commit()
            event['ready'] = True
            event['exception'] = ""
            self.conn.close()
        except Exception as ex:
            event['ready'] = False
            event['except'] = str(ex)
# microservice writefile
class writefile:
    def __init__(self, event):
        event["ready"] = True
        try:
            self.file = ""
            self.checkpath = path.exists(event["connection"]["source"])
            if event["connection"]["mode"] == "append":
                self.file = open(event["connection"]["source"], 'a+')
                self.file.write(event["command"])
                self.file.close()
                event["excep"] = ""
            elif event["connection"]["mode"] == "new":
                self.file = open(event["connection"]["source"], 'w')
                self.file.write(event["command"])
                self.file.close()
                event["exception"] = ""
        except Exception as ex:
            event["ready"] = False
            event["except"] = str(ex)
    # Package Example
    # {
    #    "service": "writefile",
    #    "connection": {"source":"logdata1.txt","Mode":"append/new"},
    #    "command": "Hello Data text gifleee"
    #    "response": "",
    #    "ready": True,
    #    "exception": ""
    # }
# microservice readfile
class readfile:
    def __init__(self, event):
        try:
            self.file = open(event["connection"]["source"], 'r')
            event["response"] = self.file.read()
            self.file.close()
            event["ready"] = True
            event["except"] = ""
        except Exception as ex:
            event["response"] = ""
            event["ready"] = False
            event["except"] = str(ex)
# microservice modbus tcp client
class modbus_tcp_client:
    # Package Example
    # {
    #    "service": "modbus_tcp_client",
    #    "connection": {"source":"192.168.1.1","port":502},
    #    "command": [
    #                  {"access":"r","addr":"400001","size":10,"value":[],"except":""},
    #                  {"access":"w","addr":"400002","size":10,"value":[],"except":""},
    #                  {"access":"r","addr":"400003","size":10,"value":[],"except":""},
    #                  {"access":"w","addr":"400004","size":10,"value":[0,1,2,0,23,434,123,343,454,343,343,3434],"except":""}
    #                ]
    #    "response": [{"access":"read","addr":"400001","value":0}],
    #    "ready": True,
    #    "exception": ""
    # }
    def __init__(self, event):
        event["ready"] = True
        for self.transaction in event["command"]:
            try:
                self.cmd = int(self.transaction["addr"][0:1])
                self.addr = int(self.transaction["addr"][1:5])
                self.len = int(self.transaction["size"])
                self.mb = ModbusClient(host=event["connection"]["source"], port=event["connection"]["port"],auto_open=True, auto_close=True)
                if self.transaction["access"] == "r":
                    if self.cmd == 4:
                        self.res = self.mb.read_holding_registers(self.addr, self.len)
                        self.transaction["value"] = self.res
                        if (len(self.res) > 0):
                            self.transaction["status"] = True
                        else:
                            self.transaction["status"] = False

                elif self.transaction["access"] == "w":
                    if self.cmd == 4:
                        self.transaction["status"] = self.mb.write_multiple_registers(self.addr,self.transaction["value"])
            except Exception as e:
                self.transaction["except"] = str(e)
                event["ready"] = False
# microservice read filename in path
class dir:
    # Package Example
    # {
    #    "service": "directories",
    #    "connection":"",
    #    "command": "/media"
    #    "response": [filename,filename,filename],
    #    "ready": True,
    #    "exception": ""
    # }
    def __init__(self, event):
        try:
            self.link = event["command"];
            event["response"] = os.listdir(self.link)
            event["ready"] = True
        except Exception as e:
            event["except"] = str(e)
            event["ready"] = False

# microservice atlascopco PF6000
class pf6000:
    # {
    #     "client": {"addr": "", "port": ""},
    #     "tstart": "",
    #     "tend": "",
    #     "Quality": 0,
    #     "events":
    #         [
    #             {
    #                 "service": "PF6000",
    #                 "connection": {"source": "192.168.1.241", "port": 4545},
    #                 "command": {"pset": 1, "tool": "True"},
    #                 "response": {},
    #                 "ready": "True",
    #                 "exception": ""
    #             }
    #         ]
    #}

    MID0001_startcomm = {"length": "", "mid": "0001", "rev": "001", "ack": "", "data": "", "stationid": "","spindleid": "", "cmd": ""}
    MID0002_acknowledge = {"length": "", "mid": "0002", "rev": "001", "ack": "1", "data": "", "stationid": "","spindleid": "", "cmd": ""}
    MID0003_stopcomm = {"length": "", "mid": "0003", "rev": "001", "ack": "", "data": "", "stationid": "","spindleid": "", "cmd": ""}
    MID0004_command_error = {"length": "", "mid": "0004", "rev": "001", "ack": "1", "data": "", "stationid": "","spindleid": "", "cmd": ""}
    MID0005_command_accept = {"length": "", "mid": "0005", "rev": "001", "ack": "1", "data": "", "stationid": "","spindleid": "", "cmd": ""}
    MID0014_psetselect_subcribe = {"length": "", "mid": "0014", "rev": "001", "ack": "1", "data": "", "stationid": "00","spindleid": "00", "cmd": ""}
    MID0015_psetselect = {"length": "", "mid": "0015", "rev": "001", "ack": "1", "data": "", "stationid": "","spindleid": "", "cmd": ""}
    MID0018_pset_request = {"length": "", "mid": "0018", "rev": "001", "ack": "1", "data": "", "stationid": "","spindleid": "", "cmd": ""}
    MID0042_disabletools = {"length": "", "mid": "0042", "rev": "001", "ack": "1", "data": "", "stationid": "","spindleid": "", "cmd": ""}
    MID0043_enabletools = {"length": "", "mid": "0043", "rev": "001", "ack": "1", "data": "", "stationid": "","spindleid": "", "cmd": ""}
    MID0060_last_tightening_result = {"length": "", "mid": "0060", "rev": "001", "ack": "", "data": "","stationid": "00", "spindleid": "00", "cmd": ""}
    MID0061_last_tightening_result = {"length": "", "mid": "0061", "rev": "001", "ack": "1", "data": "","stationid": "", "spindleid": "", "cmd": ""}
    MID0064_old_tightening_result = {"length": "", "mid": "0064", "rev": "001", "ack": "", "data": "         0","stationid": "", "spindleid": "", "cmd": ""}
    MID0214_io_status = {"length": "", "mid": "0214", "rev": "001", "ack": "", "data": "00", "stationid": "","spindleid": "", "cmd": ""}
    MID0215_io_status_reply = {"length": "", "mid": "0215", "rev": "001", "ack": "1", "data": "", "stationid": "","spindleid": "", "cmd": ""}
    # pf6000_dev = {"addr":"192.168.1.241","port":4545,"connection":False}
    pf6000_dev = {"addr": "0.0.0.0", "port": 0}
    pf6000_tightening = {"psetid": 0, "datetime": ""}
    pf6000_output = {"relay1": False, "relay2": False, "relay3": False, "relay4": False};
    pf6000_result = {
        "tighteningID": "",
        "vinnumber": "",
        "psetid": 0,
        "batchcounter": 0,
        "tighteningstatus": "",
        "torquestatus": "",
        "anglestatus": "",
        "angle": 0,
        "torque": 0,
        "timestamp": "",
        "batchstatus": ""
    }
    pf6000_log = {"tighteningID": 0, "changelog": False, "ready1": False, "ready2": False, "exception1": "","exception2": ""}
    pf6000_cmd_pset = {"value": 0, "change": False}
    pf6000_cmd_tool = {"value": 0, "change": False}
    pf6000_process = {"value": 0, "change": False}

    def encode_open_protocol(self,source):
        source["cmd"] = ""
        source["cmd"] = source["mid"] + source["rev"] + \
                        (" " if source["ack"] == "" else source["ack"]) + \
                        ("  " if source["stationid"] == "" else source["stationid"]) + \
                        ("  " if source["spindleid"] == "" else source["spindleid"]) + \
                        "    " + \
                        ("\0" if source["data"] == "" else source["data"] + "\0")
        source["cmd"] = str(len(source["cmd"]) + 3).zfill(4) + source["cmd"]

    def decode_open_protocol(self,source):
        MIDreturn = {"length": "", "mid": "", "rev": "", "ack": "", "data": "", "stationid": "",
                     "spindleid": "", "cmd": ""}
        try:
            packagelen = int(source[0:4])
            datalen = len(source)
            if ((packagelen != datalen) and (datalen >= 16)):
                return False, None
            MIDreturn["length"] = source[0:4]
            MIDreturn["mid"] = source[4:8]
            MIDreturn["rev"] = source[8:12]
            MIDreturn["ack"] = source[12:13]
            MIDreturn["stationid"] = source[13:15]
            MIDreturn["spindleid"] = source[15:17]
            MIDreturn["data"] = source[20:datalen]
            MIDreturn["cmd"] = source
            return True, MIDreturn
        except Exception as error:
            print("Open Protocol : Error " + str(error))
            return False, None

    def __init__(self,event):
            try:
                self.recv = ""
                self.tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                self.tcp.settimeout(5)
                self.ip = event["connection"]["source"]
                self.port = event["connection"]["port"]
                self.tcp.connect((self.ip,int(self.port)))

                # print("MID0001 Start Communication\r")
                # MID0001 Start Communication
                self.encode_open_protocol(self.MID0001_startcomm)
                self.tcp.sendall(self.MID0001_startcomm["cmd"].encode())
                time.sleep(0.05)
                self.recv = self.recv + self.tcp.recv(1024).decode()

                # print("MID0014 Pset Upload\r")
                # MID0014 Pset Upload
                self.encode_open_protocol(self.MID0014_psetselect_subcribe)
                self.tcp.sendall(self.MID0014_psetselect_subcribe["cmd"].encode())
                time.sleep(0.05)
                self.recv = self.recv + self.tcp.recv(1024).decode()

                # print("MID0214 Status IO\r")
                # MID0214 Status IO
                self.encode_open_protocol(self.MID0214_io_status)
                self.tcp.sendall(self.MID0214_io_status["cmd"].encode())
                time.sleep(0.05)
                self.recv = self.recv + self.tcp.recv(1024).decode()

                # print("MID0064  Old tightening\r")
                # MID0064  Old tightening
                self.encode_open_protocol(self.MID0064_old_tightening_result)
                self.tcp.sendall(self.MID0064_old_tightening_result["cmd"].encode())
                time.sleep(0.05)
                self.recv = self.recv + self.tcp.recv(1024).decode()

                self.response = self.recv.split("\0")
                self.MIDGROUP = []

                for self.text in self.response:
                    if self.text != "":
                        self.res, self.MID = self.decode_open_protocol(self.text)
                        if (self.res == True):
                            self.MIDGROUP.append(self.MID)

                for self.MID in self.MIDGROUP:
                    if (self.MID["mid"] == "0215"):
                        # ("\0" if source["data"] == "" else source["data"] + "\0")
                        self.pf6000_output["relay1"] = True if self.MID["data"][9:10] == "1" else False
                        self.pf6000_output["relay2"] = True if self.MID["data"][13:14] == "1" else False
                        self.pf6000_output["relay3"] = True if self.MID["data"][17:18] == "1" else False
                        self.pf6000_output["relay4"] = True if self.MID["data"][21:22] == "1" else False
                        print("MID" + self.MID["mid"] + " : " + str(self.pf6000_output) + "\r")
                    elif (self.MID["mid"] == "0015"):
                        self.pf6000_tightening["psetid"] = int(self.MID["data"][0:3])
                        self.pf6000_tightening["datetime"] = self.MID["data"][3:]
                        print("MID" + self.MID["mid"] + " : " + str(self.pf6000_tightening) + "\r")
                    elif (self.MID["mid"] == "0065"):
                        # pf6000_result = {
                        #    "tighteningID": "",
                        #    "vinnumber": "",
                        #    "psetid": 0,
                        #    "batchcounter": 0,
                        #    "tighteningstatus": "",
                        #    "torquestatus": "",
                        #    "anglestatus": "",
                        #    "angle": 0,
                        #    "timestamp": "",
                        #    "batchstatus": ""
                        # }
                        self.pf6000_result["tighteningID"] = int(self.MID["data"][2:12])
                        self.pf6000_result["psetid"] = int(self.MID["data"][41:44])
                        self.pf6000_result["batchcounter"] = int(self.MID["data"][46:50])
                        self.pf6000_result["tighteningstatus"] = "OK" if self.MID["data"][52:53] == "1" else "NOK"
                        self.pf6000_result["torquestatus"] = "OK" if (self.MID["data"][55:56] == "1") else "LOW" if (self.MID["data"][55:56] == "0") else "HIGH"
                        self.pf6000_result["anglestatus"] = "OK" if (self.MID["data"][58:59] == "1") else "LOW" if (self.MID["data"][58:59] == "0") else "HIGH"
                        self.pf6000_result["torque"] = int(self.MID["data"][61:67]) / 100
                        self.pf6000_result["angle"] = int(self.MID["data"][69:74])
                        self.pf6000_result["timestamp"] = self.MID["data"][76:95]
                        self.pf6000_result["batchstatus"] = "OK" if (self.MID["data"][97:98] == "1") else "NOK" if (self.MID["data"][97:98] == "0") else "NOTUSE"
                        print("MID" + self.MID["mid"] + " : " + str(self.pf6000_result) + "\r")

                # External Change value
                self.recv = ""
                if self.pf6000_tightening["psetid"] != event["command"]["pset"]:
                    self.MID0018_pset_request["data"] = str(event["command"]["pset"]).zfill(3)
                    self.encode_open_protocol(self.MID0018_pset_request)
                    self.tcp.sendall(self.MID0018_pset_request["cmd"].encode())
                    time.sleep(0.05)
                    self.recv = self.recv + self.tcp.recv(1024).decode()


                self.tool = self.MID0043_enabletools if (event["command"]["tool"] == 1) else self.MID0042_disabletools
                self.encode_open_protocol(self.tool)
                self.tcp.sendall(self.tool["cmd"].encode())
                time.sleep(0.05)
                self.recv = self.recv + self.tcp.recv(1024).decode()



                self.tcp.close()

                event["ready"] = True
                event["response"] = {"tightening": self.pf6000_tightening, "output": self.pf6000_output, "result": self.pf6000_result}
                event["exception"] = ""

            except Exception as e :
                event["ready"] = False
                event["exception"] = str(e)

class stream:
    #            {
    #                "service": "stream",
    #                "connection": {"block":0,"cmd":"read/write"},
    #                "command": " string if write ",
    #                "response": " string if read ",
    #                "ready": 0,
    #                "exception": ""
    #            }
    block = []
    maxsize = 0
    def __init__(self,size):
        self.block = [None]*size;
        self.maxsize = size;

    def service(self,event):
        event["exception"]
        event["ready"] = False
        try:
            if (int(event["connection"]["block"]) <= self.maxsize-1) and (int(event["connection"]["block"]) > -1) :
                if event["connection"]["cmd"] == "read" :
                    event["response"] = self.block[int(event["connection"]["block"])]
                    event["ready"] = True
                elif event["connection"]["cmd"] == "write" :
                    self.block[int(event["connection"]["block"])] = event["command"]
                    event["response"] = ""
                    event["ready"] = True
            else:
                event["exception"] = "offset fail"
                event["ready"] = False
        except Exception as e :
            event["exception"] = str(e)
            event["ready"] = False
drive = stream(100)

def server():
    ethernet_service , port_service = utility_network().UISelectIPMachine()
    hostaddr = ethernet_service['ip']
    port = int(port_service)
    print("**************************************************************************************************")
    print("Software : FactoryComm")
    print("Server : " + str(hostname) + "\r")
    print("Service Path : " + str(hostaddr) + ":" + str(port) + "\r")
    print("API Verison : 2.5" + "\r")
    print("**************************************************************************************************")
    s = socket.socket()
    s.bind(('', port))
    s.listen(10)
    eventcount = 0
    while True:
        # package test mssql
        # {
        #    "client": {"addr": "", "port": ""},
        #    "tstart": "",
        #    "tend": "",
        #    "Quality": 0,
        #    "events":
        #        [
        #            {
        #                "service": "mssql",
        #                "connection": {"source": "192.168.1.164", "user": "sa", "pass": "1234", "db": "ODS"},
        #                "command": "SELECT * FROM [ODS].[dbo].[Path_Setting_DA] where Step = 5",
        #                "response": "",
        #                "ready": 0,
        #                "exception": ""
        #            }
        #        ]
        # }
        res, client = s.accept()
        time.sleep(0.5)
        recive = res.recv(1000000)
        if not recive:
            res.close()
        else:
            try:
                req = HttpPackage(recive)
                #data = req.getdata()
                method,url,data  = req.geturl()
                print("client : " + str(client[0]) + ":" + str(client[1]) + " Time : " + datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
                print("method : " + method+"\r")
                print("url : " + url+"\r")
                print("method : " + data+"\r\n")
                uid = json.loads(data)
                uid['tstart'] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                uid['client']['addr'] = client[0]
                uid['client']['port'] = client[1]
                eventcount=0
                for event in uid['events']:
                    if event['service'] == "mssql":
                        mssql(event)
                        # Package Example
                        # {
                        #    "service": "mssql",
                        #    "connection": {"source": "192.168.1.164", "user": "sa", "pass": "1234", "db": "ODS"},
                        #    "command": "SELECT * FROM [ODS].[dbo].[Path_Setting_DA] where Step = 5",
                        #    "response": "",
                        #    "ready": True,
                        #    "except": ""
                        # }
                    elif event['service'] == "writefile":
                        writefile(event)
                        # Package Example
                        # {
                        #    "service": "writefile",
                        #    "connection": {"source":"logdata1.txt","Mode":"append/new"},
                        #    "command": "Hello Data text gifleee"
                        #    "response": "",
                        #    "ready": True,
                        #    "except": ""
                        # }
                    elif event['service'] == "readfile":
                        readfile(event)
                        # Package Example
                        # {
                        #    "service": "readfile",
                        #    "connection": {"source":"logdata1.txt"},
                        #    "command": "",
                        #    "response": "Hello Data text gifleee",
                        #    "ready": True,
                        #    "except": ""
                        # }
                    elif event['service'] == "iphost":
                        event['response'] = client[0]
                        event['ready'] = True
                        event['exception'] = ""
                    elif event['service'] == "modbus_tcp_client":
                        # Package Example
                        # {
                        #    "service": "modbus_tcp_client",
                        #    "connection": {"source":"192.168.1.1","port":502},
                        #    "command": [
                        #                  {"access":"r","addr":"400001","numberblock":10,"value":[],"except":""},
                        #                  {"access":"w","addr":"400002","numberblock":10,"value":[],"except":""},
                        #                  {"access":"r","addr":"400003","numberblock":10,"value":[],"except":""},
                        #                  {"access":"w","addr":"400004","numberblock":10,"value":[0,1,2,0,23,434,123,343,454,343,343,3434],"except":""}
                        #                ]
                        #    "response": [{"access":"read","addr":"400001","value":0}],
                        #    "ready": True,
                        #    "except": ""
                        # }
                        modbus_tcp_client(event)
                    elif event['service'] == "directories":
                        # Package Example
                        # {
                        #    "service": "directories",
                        #    "connection":"",
                        #    "command": "/media"
                        #    "response": [filename,filename,filename],
                        #    "ready": True,
                        #    "exception": ""
                        # }
                        dir(event)
                    elif event['service'] == "omron_fins_udp" :
                        # Package Example
                        # {
                        #    "service": "omron_fins_udp",
                        #    "connection": {"source":"192.168.1.1","port":502},
                        #    "command": [
                        #                  {"access":"r","addr":"D20000","size":10,"value":[0,1,2,3,4,5,6,7,8,9],"except":""},
                        #                  {"access":"w","addr":"CIO100","size":10,"value":[],"except":""},
                        #                  {"access":"r","addr":"D0","size":10,"value":[],"except":""},
                        #                  {"access":"w","addr":"D1000","size":10,"value":[0,1,2,0,23,434,123,343,454,343,343,3434],"except":""}
                        #                ]
                        #    "response": [{"access":"read","addr":"400001","value":0}],
                        #    "ready": True,
                        #    "exception": ""
                        # }
                        omron_fins_udp(event)
                    elif event['service'] == "ping" :
                        # Package Example
                        # {
                        #    "service": "ping",
                        #    "connection":"",
                        #    "command": [
                        #                  {"addr":"192.168.1.1","value":0,"except":""},
                        #                  {"addr":"192.168.1.2","value":0,"except":""},
                        #                  {"addr":"192.168.1.3","value":0,"except":""},
                        #                  {"addr":"192.168.1.4","value":0,"except":""},
                        #                ]
                        #    "response": {"ok":0,"ng":0},
                        #    "ready": True,
                        #    "exception": ""
                        # }
                        os_ping(event)
                    elif event['service'] == "PF6000" :
                        # Package Example
                        # {
                        #    "service": "PF6000",
                        #    "connection":{"source":"192.168.1.1","port":502},
                        #    "command": {pset=1,tool=True}
                        #    "response": {"ok":0,"ng":0},
                        #    "ready": True,
                        #    "exception": ""
                        # }
                        pf6000(event)
                    elif event['service'] == "stream" :
                        #            {
                        #                "service": "stream",
                        #                "connection": {"block":0,"cmd":"read/write"},
                        #                "command": " string if write ",
                        #                "response": " string if read ",
                        #                "ready": 0,
                        #                "exception": ""
                        #            }
                        drive.service(event)
                    elif event['service'] == "mitsubishi_fx5u_slmp_tcp" : 
                        # Package Example
                        # {
                        #    "service": "mitsubishi_fx5u_slmp",
                        #    "connection": {"source":"192.168.1.198","port":20000},
                        #    "command": [
                        #                  {"access":"r","addr":"D20000","size":10,"value":[0,1,2,3,4,5,6,7,8,9],"except":""},
                        #                  {"access":"w","addr":"D1000","size":10,"value":[0,1,2,0,23,434,123,343,454,343,343,3434],"except":""}
                        #                ]
                        #    "response": [],
                        #    "ready": 0,
                        #    "exception": ""
                        # }
                        mitsubishi_slmp_tcp(event)
                    else:
                        event['ready'] = False
                        event['exception'] = "Service NotFound"
                    eventcount = eventcount + 1
                # final SendBack
                uid['tend'] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                SendbackToClientAndCloseConnection(res, uid)
            except Exception as ex:
                print("Found error : " + str(ex))
                SendbackToClientAndCloseConnection(res, {'error': str(ex)})
            # my_code = 'print(event)'
            # exec(my_code)


PID_server = Thread(target=server)
PID_ping = Thread(target=server_ping)
PID_server.start()
PID_ping.start()

print("service backup : started\r")
while (True):
    if (PID_server.is_alive() == False):
            PID_server = Thread(target=server)
            PID_server.run()

    if (PID_ping.is_alive() == False):
            PID_ping = Thread(target=server_ping)
            PID_ping.run()

    time.sleep(1)
