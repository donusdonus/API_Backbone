import time
import socket
import re
from threading import Thread

class FH_Omron_Vision:

        def __init__(self,ip):
                self.response = []
                self.database = []
                self.start = 0
                self.interval = 1
                self.ip = ip
                self.port_input = 9600
                self.port_output = 9601
                self.port_buffersize = 1023
                self.threadRecive = Thread(target=self.GetResult)
                self.threadRecive.start()
                self.threadTrigger = Thread(target=self.Trigger)
                self.threadTrigger.start()



        def Command(self,cmd,delay=0.1):
                self.camera_input_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                self.camera_input_socket.sendto(cmd.encode('utf-8'),(self.ip,self.port_input))
                time.sleep(delay)
                self.camera_input_socket.close()



        def req(self,event):

            self.s = 0
            self.sg = 0

            try:
                     self.start = int(event['command']['start'])
                     self.interval = int(event['command']['interval'])
                     if self.start == 1 :
                        self.response.clear()
                        self.Command("S")
                        self.s = self.response[0]
                        self.response.clear()
                        self.Command("SG")
                        self.sg = self.response[0]

                        self.scence_check = (self.s == int(event['command']['scence']))
                        self.group_scence_check = (self.sg == int(event['command']['groupscence']))

                        if self.scence_check == False or self.group_scence_check == False :
                            self.Command("SG " + str((event['command']['groupscence'])))
                            self.Command("S " + str(event['command']['scence']))

                     elif self.start == 0 :
                            self.database = []

                     event['command']['response'] = {'config':{'groupscence':self.sg,'scence':self.s},'result':self.database}
                     event['command']['exception'] = ""
                     event['command']['ready'] = 1
            except Exception as ex :
                        event['command']['exception'] = str(ex)
                        event['command']['ready'] = 0

        def Protect_ProcessDown(self):
                try:
                        if(self.threadRecive.is_alive() == False):
                                self.threadRecive = Thread(target=self.GetResult)
                                self.threadRecive.run()

                        if(self.threadTrigger.is_alive() == False):
                                self.threadTrigger = Thread(target=self.Trigger)
                                self.threadTrigger.run()

                except Exception as ex:
                        print("Camera Protect Process : " + str(ex))

        def Trigger(self):
                    while True :
                        time.sleep(self.interval)
                        if self.start == 1 :
                            self.Command('MEASURE')
                            print("Trigger Camera IP : " + self.ip)


        def GetResult(self):
                self.camera_output_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                self.camera_output_socket.bind(('',self.port_output))
                while True :
                     self.camera_output_result , self.camera_output_address =  self.camera_output_socket.recvfrom(self.port_buffersize)

                     try:

                         self.text = self.camera_output_result.decode('utf-8')
                         if(self.text.find('\r') == -1):
                                 #do something
                                 if self.text in self.response :
                                        self.a=1
                                 else :
                                        self.response.append(self.text)
                         else:
                             if self.start == 0 :
                                self.database = []
                             elif self.start == 1 :
                                self.database = self.text.replace(' ', '').replace('\r','').split(',')

                     except Exception as ex:
                             print("Camera Read Process : " + str(ex))

##########################################################################

## SG XX <group number> // select group scence
## S XXX <scence number> // select sence



