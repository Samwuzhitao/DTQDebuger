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

class QtqBurner(QWidget):
    def __init__(self, parent=None):
        global ser

        super(QtqBurner, self).__init__(parent)
        input_count = 0
        self.ports_dict = {}
        self.setWindowTitle(u"答题器烧录工具v0.1.0")
        self.file_button = QPushButton(u"打开文件")
        self.textEdit = QTextEdit()
       
        vbox = QVBoxLayout()
        vbox.addWidget(self.file_button)
        vbox.addWidget(self.textEdit)
        self.setLayout(vbox)

        self.file_button.clicked.connect(self.choose_file)


    def uart_scan(self):
        for i in range(256):
            
            try:
                s = serial.Serial(i)
                self.com_combo.addItem(s.portstr)
                self.ports_dict[s.portstr] = i
                s.close()
            except serial.SerialException:
                pass

    def choose_file(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file', './')
        file = open(filename)
        data = file.read()
        self.textEdit.setText(data)
        file.close()
 
if __name__=='__main__':
    app = QApplication(sys.argv)
    datdebuger = QtqBurner()
    datdebuger.show()
    app.exec_()

