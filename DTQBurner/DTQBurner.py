# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import serial
import string
import os
import sys
from time import sleep
from PyQt4.QtCore import *
from PyQt4.QtGui  import *


from JsonDecode import *

ser              = 0

class DtqDebuger(QWidget):
    def __init__(self, parent=None):
        global ser

        super(DtqDebuger, self).__init__(parent)
        input_count = 0
        self.ports_dict = {}
        self.setWindowTitle(u"答题器调试工具v0.1.2")

    def uart_scan(self):
        for i in range(256):
            
            try:
                s = serial.Serial(i)
                self.com_combo.addItem(s.portstr)
                self.ports_dict[s.portstr] = i
                s.close()
            except serial.SerialException:
                pass

 
if __name__=='__main__':
    app = QApplication(sys.argv)
    datdebuger = DtqDebuger()
    datdebuger.show()
    app.exec_()

