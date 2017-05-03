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
input_count      = 0

class QtqBurner(QWidget):
    def __init__(self, parent=None):
        global ser

        super(QtqBurner, self).__init__(parent)
        input_count = 0
        self.ports_dict = {}

        self.setWindowTitle(u"答题器烧录工具v0.1.0")

        self.com_combo=QComboBox(self) 
        self.com_combo.setFixedSize(75, 20)
        self.uart_scan()
        self.start_button= QPushButton(u"打开接收器")
        self.file_button = QPushButton(u"打开文件")
        self.save_button = QPushButton(u"保存文件")
        
        c_hbox = QHBoxLayout()
        c_hbox.addWidget(self.com_combo)
        c_hbox.addWidget(self.start_button)
        c_hbox.addWidget(self.file_button)
        c_hbox.addWidget(self.save_button)

        self.dtq_id_lineedit = QLineEdit(u"设备ID")
        self.browser = QTextBrowser()
        self.burn_button = QPushButton(u"烧录文件")
        vbox = QVBoxLayout()
        vbox.addWidget(self.dtq_id_lineedit)
        vbox.addWidget(self.browser)
        vbox.addWidget(self.burn_button)

        box = QVBoxLayout()
        box.addLayout(c_hbox)
        box.addLayout(vbox)

        self.setLayout(box)
        self.resize( 400, 500 )

        self.file_button.clicked.connect(self.choose_file)
        self.start_button.clicked.connect(self.open_uart)

    def uart_scan(self):
        for i in range(256):
            
            try:
                s = serial.Serial(i)
                self.com_combo.addItem(s.portstr)
                self.ports_dict[s.portstr] = i
                s.close()
            except serial.SerialException:
                pass

    def open_uart(self):
        global ser
        global decode_type_flag
        global input_count

        serial_port = str(self.com_combo.currentText())

        try:
            ser = serial.Serial( self.ports_dict[serial_port], 115200)
        except serial.SerialException: 
            pass

        if input_count == 0:
            if ser.isOpen() == True:
                self.browser.append("<font color=red> Open  <b>%s</b> \
                    OK!</font>" % ser.portstr )
                self.start_button.setText(u"关闭接收器")
                #self.uart_listen_thread.start()
                input_count = input_count + 1
        else:
            self.browser.append("<font color=red> Close <b>%s</b> \
                OK!</font>" % ser.portstr )
            self.start_button.setText(u"打开接收器")
            input_count = 0
            ser.close()


    def choose_file(self):
        filename = QFileDialog.getOpenFileName(self, 'Open file', './')
        file = open(filename)
        data = file.read()
        self.browser.setText(data)
        file.close()
 
if __name__=='__main__':
    app = QApplication(sys.argv)
    datdebuger = QtqBurner()
    datdebuger.show()
    app.exec_()

