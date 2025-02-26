from textual.app import App, ComposeResult
from textual.widgets import Header, Tree, DataTable
from textual.containers import Container
import random
import threading 
import time
import asyncio

class API_Backbone(App):
    """สร้าง Terminal GUI ที่รองรับ Live Table และ TreeNode"""

    CSS = """
    Screen {
        layout: vertical;
    }

    #header {
        height: 3;
        background: cyan;
        text-align: center;
    }

    #main_container {
        layout: horizontal;
        height: 100%;
    }

    #sidebar {
        width: 30%;
        background: green;
        height: 100%;
    }

    #content {
        width: 70%;
        background: blue;
        height: 100%;
    }
    """
    sername = []
    stack = []
    information = []
    service = []
    monitor = []

    def compose(self) -> ComposeResult:
        """สร้างโครงสร้าง UI"""
        yield Header(id="header", name="🚀 Live Table App")

        with Container(id="main_container"):
            with Container(id="sidebar"):
                tree = Tree("📂 Server", id="file_tree")
                folder1 = tree.root.add("📁 infomation")
                for x in self.information :
                    folder1.add_leaf("📄 " + str(x))
                
                folder2 = tree.root.add("📁 Service")
                for x in self.service : 
                    folder2.add_leaf("📄 " + str(x))
          
                #folder2.add_leaf("📄 File 2.1")

                tree.root.expand_all()

                yield tree

            with Container(id="content"):
                self.data_table = DataTable()
                yield self.data_table

    def on_mount(self) -> None:
        """ตั้งค่าเมื่อแอปเริ่มทำงาน"""
        self.sername = []
        self.data_table.add_columns("No", "Address", "Port", "Service Name ","Status","Time Start ","Operation Time","Content")

        # เพิ่มข้อมูลเริ่มต้น 10 แถว
        self.rows = []
        for _ in range(100):
            row_data = [random.randint(1, 100) for _ in range(5)]
            row_key = self.data_table.add_row(*row_data)  # เพิ่มแถวแล้วได้ row_key
            self.rows.append(row_key)  # เก็บ row_key ไว้ใช้ใน update_table

        # ตั้งค่าให้ Table อัปเดตข้อมูลทุก 1 วินาที
        self.set_interval(1, self.update_table)

    def addservicename(self,str) -> None :
        self.service.append(str)
        
    def addinfo(self,str) -> None :
        self.information.append(str)

            
    def addtrace(self,address="",port="",service="",status="",tstart="",operationtime="",content="") -> None : 
            self.monitor.append(
                                {
                                 "address":address,
                                 "port":port,
                                 "service":service,
                                 "status":status,
                                 "tstart":tstart,
                                 "operationtime":operationtime,
                                 "content":content
                                 })
            

    async def update_table(self) -> None:
        """อัปเดตข้อมูลใน Table แบบ Realtime"""
        await asyncio.sleep(0.1)
        for ds in self.service : 
            er=0
            
        '''
        for row_index, row_key in enumerate(self.rows):
            if row_key in self.data_table.rows:  # ตรวจสอบว่า row_key มีอยู่จริง
                new_data = [random.randint(1, 100) for _ in range(8)]
                column_keys = list(self.data_table.columns.keys())  # ดึง column_key ที่ถูกต้อง

                for col_index, value in enumerate(new_data):
                    column_key = column_keys[col_index]  # ใช้ key แทน index
                    self.data_table.update_cell(row_key, column_key, value)
        '''


def display():
    ui = API_Backbone();
    ui.addinfo("Gateways=HTTP")
    ui.addinfo("IP=192.168.1.23")
    ui.addinfo("Port=8000")
    
    ui.addservicename("test")
    ui.addservicename("A")
    ui.addservicename("testB")
    
    ui.addtrace(str="192.168.1.1",port="test",service="test2",status="ax",tstart="start",operationtime="optime",content="content")
    
    ui.run()

if __name__ == "__main__":
    display()
    #ui_process = threading.Thread(target=display)
    #ui_process.start()
    #ui.addservicename("erer");

    

