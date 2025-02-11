import traceback
import datetime
import os , sys
from datetime import date, timedelta


class HistoryLog:
    def __init__(self, filename):
        self.filename = filename
        # FLAG ENABLE LOG FUNCTION
        self.enable = True
        self.logcount = 1
        # FLAG PRINT DATA LOG ON TERMINAL
        self.printlog = True
        # FLAG PRINT ONLY NO LOG
        self.printonly = False
        self.FixLogSizeMB = 10000000

    def insert(self, topic, level, data):

        try:
            self.Updatelog = False

            if self.enable == False:
                return

            self.now = datetime.datetime.now(datetime.timezone(timedelta(hours=7)))
            self.strlog = "[" + str(self.logcount) + "][" + topic + "]" + "[" + level + "][" + str(
                self.now) + "] : " + data + "\r"
            self.fn = self.filename + "-" + str(date.today()) + ".txt"

            if self.printonly == False:
                # file = open('heelo',"a+")
                self.file = open(str(self.fn),'a')
                self.file.write(self.strlog)
                self.file.close()
                self.Updatelog = True

            if self.printlog == True:
                print(self.strlog)
                self.Updatelog = True

            if self.Updatelog:
                self.logcount = self.logcount + 1

        except Exception as ex:
            self.now = datetime.datetime.now(datetime.timezone(timedelta(hours=7)))
            self.strlog = "[" + str(self.logcount) + "][SYSTEM]" + "[ERROR][" + str(self.now) + "] : [" + str(
                traceback.extract_stack()[-1][1]) + "][" + self.fn + "][" + str(ex) + "]\r"
            print(self.strlog)
            self.logcount = self.logcount + 1


