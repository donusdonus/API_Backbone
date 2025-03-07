import os
from PIL import Image
import zpl
import socket


def System_EODS(QRCode,Line1,Line2,Line3):
    l =zpl.Label(30,30)
    l.origin(6,1) 
    l.barcode('Q',QRCode, magnification=3)
    l.endorigin()
    
    l.origin(6,11)
    l.write_text(Line1, char_height=2, char_width=2, line_width=32, justification='L')
    l.endorigin()
    
    
    l.origin(6,14)
    l.write_text(Line2, char_height=2, char_width=2, line_width=32, justification='L')
    l.endorigin()
    
    
    l.origin(6,17)
    l.write_text(Line3, char_height=2, char_width=2, line_width=32, justification='L')
    l.endorigin()
    
    
    print(l.dumpZPL())
    
    return l.dumpZPL()
    

def System_ECheckSheet():
    x=0


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
sock.connect(('10.107.113.76', 9100))  
#sock.send('Test\n')  
sock.send(str.encode(System_EODS(
                                  "W214-PC214001402-99999998-EOL1-2025/11/08",
                                  "9999998",
                                  "E 220d AMG Line",
                                  "")))  
sock.close()

# EODS
# QR
# ModelCode-FGCode-ProdCode-FDOK-Station-Datetime
# Line 1 FDOK
# Line 2 Product Name ( Child Name )
# Line 3 Prodcut Name ( Child Name )

# ECHECKSHEET
# QR
# ModelCode-FGCode-FDOK-Station-Datetime
# Line 1 FDOK
# Line 2 Model Name
# Line 3 Model Name


'''
text_packet =  {'mode': 'T | Q | B ', 'data': 'Toon.Automation' , 'option':{'x':0,'y':0,'ch':2,'cw':2,'lw':2,'aligments':'C'},
               {'mode': 'Q', 'data': 'Toon.Automation' , 'option':{'x':0,'y':0,'size':3}
'''
'''
l.origin(5,2)
l.write_text("Station 14", char_height=2, char_width=3, line_width=20, justification='C')
l.endorigin()
'''

'''
height += 13
image_width = 5
l.origin((l.width-image_width)/2, height)
image_height = l.write_graphic(
    Image.open(os.path.join(os.path.dirname(zpl.__file__), 'trollface-large.png')),
    image_width)
l.endorigin()
'''
'''
height += image_height + 5
l.origin(10, height)
l.barcode('U', '07000002198', height=70, check_digit='Y')
l.endorigin()
'''

'''
l.origin(8,5)
l.barcode('Q', 'Toon.Automation', magnification=6)
l.endorigin()
'''

'''
height += 20
l.origin(0, height)
l.write_text('Happy Troloween!', char_height=5, char_width=4, line_width=60,
             justification='C')
l.endorigin()
'''
'''
print(l.dumpZPL())
l.preview()
'''

