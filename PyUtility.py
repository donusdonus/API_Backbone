import tkinter

import ifaddr
from tkinter import *
from tkinter import ttk
class utility_network:

    def __init__(self):
        self.adapters = []
        self.network = []

    def GetIPMachine(self):
        self.adapters = ifaddr.get_adapters()
        for enet in self.adapters :
            for addr in enet.ips :
                if addr.is_IPv4 :
                     self.network.append({'enet':addr.nice_name,'ip':addr.ip})
        return  self.network

    def UISelectIPMachine(self):
        self.root = Tk()
        self.root.geometry("700x80")
        self.root.title("API IPService")
        self.Label_Address = Label(self.root,text="Ethernet Network",font=8)
        self.Label_Port = Label(self.root, text="Service Port", font=8)
        self.ListValue = self.GetIPMachine()
        self.Combobox = ttk.Combobox(self.root,textvariable=StringVar(value="Select"),state="readonly",justify='center',values=self.ListValue,width=50,font=10)
        self.Button = ttk.Button(self.root,text="Accept",width=10,command=self.UIClick)
        self.numeric = ttk.Spinbox(self.root,from_=0,to=65535,font=20)
        self.numeric.set(20001)
        self.Combobox.grid(row=0,column=1,sticky=W+E)
        self.Label_Address.grid(row=0,column=0,sticky=W+E)
        self.Button.grid(row=0,column=2,sticky=W+E)
        self.Label_Port.grid(row=1,column=0,sticky=W+E)
        self.numeric.grid(row=1,column=1,sticky=W)
        self.root.mainloop()

        for self.index in self.GetIPMachine() :
                if str(self.index) == self.ret_ui_selector :
                        self.ret_ui_selector_json = self.index


        return  self.ret_ui_selector_json , self.ret_ui_port
    def UIClick(self):

        if(self.Combobox.get() == ""):
            return

        try:
            int(self.numeric.get())
        except Exception as e:
            print("Fault Type of Port Service : " + str(e))
            return

        self.ret_ui_selector = self.Combobox.get()
        self.ret_ui_port = self.numeric.get()
        self.root.destroy()

