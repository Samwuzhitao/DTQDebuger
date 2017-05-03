# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import serial
import string
import time
import os
import sys
from time import sleep
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
import json

from JsonDecode import *

ser              = 0
input_count      = 0

class UartListen(QThread): 
    def __init__(self,parent=None): 
        super(UartListen,self).__init__(parent) 
        self.working=True 
        self.num=0 
        self.json_revice = JsonDecode()
        self.ReviceFunSets           = {
            0:self.uart_down_load_image_0
        }

    def __del__(self): 
        self.working=False 
        self.wait()

    def uart_down_load_image_0(self,read_char):
        recv_str      = ""
        ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'

        str1 = self.json_revice.r_machine(read_char)

        if len(str1) != 0:
            now = time.strftime( ISOTIMEFORMAT,
                time.localtime(time.time()))
            recv_str = u"<b>R[%d]: </b>" % (input_count-1) + u"%s" % str1

        return recv_str

    def run(self): 
        global ser

        while self.working==True: 
            if ser.isOpen() == True:
                read_char = ser.read(1)
                recv_str = self.ReviceFunSets[0]( read_char )
                if len(recv_str) > 0:
                    self.emit(SIGNAL('output(QString)'),recv_str)

class QtqBurner(QWidget):
    def __init__(self, parent=None):
        global ser

        super(QtqBurner, self).__init__(parent)
        input_count = 0
        self.ports_dict = {}
        self.filename   = ''

        self.setWindowTitle(u"答题器烧录工具v0.1.0")

        self.com_combo=QComboBox(self) 
        self.com_combo.setFixedSize(75, 20)
        self.uart_scan()
        self.start_button= QPushButton(u"打开接收器")
        self.file_button = QPushButton(u"打开文件")
        self.save_button = QPushButton(u"转换文件")
        
        c_hbox = QHBoxLayout()
        c_hbox.addWidget(self.com_combo)
        c_hbox.addWidget(self.start_button)
        c_hbox.addWidget(self.file_button)
        c_hbox.addWidget(self.save_button)

        self.dtq_id_label=QLabel(u"设备ID:") 
        self.dtq_id_lineedit = QLineEdit(u"1122334455667788")
        e_hbox = QHBoxLayout()
        e_hbox.addWidget(self.dtq_id_label)
        e_hbox.addWidget(self.dtq_id_lineedit)

        self.browser = QTextBrowser()
        self.burn_button = QPushButton(u"烧录文件")
        vbox = QVBoxLayout()
        vbox.addWidget(self.browser)
        vbox.addWidget(self.burn_button)

        box = QVBoxLayout()
        box.addLayout(c_hbox)
        box.addLayout(e_hbox)
        box.addLayout(vbox)

        self.setLayout(box)
        self.resize( 400, 500 )

        self.file_button.clicked.connect(self.choose_file)
        self.start_button.clicked.connect(self.band_start)
        self.save_button.clicked.connect(self.exchange_file)
        self.uart_listen_thread=UartListen()
        self.connect(self.uart_listen_thread,SIGNAL('output(QString)'),
            self.uart_update_text) 
        self.com_combo.currentIndexChanged.connect(self.change_uart)

    def change_uart(self):
        global input_count
        global ser

        if ser != 0:
            input_count = 0
            ser.close()
        if input_count == 0:
            self.open_uart()

    def uart_update_text(self,data):
        self.browser.append(data)
        if len(data) == 56:
            self.dtq_id_lineedit.setText(data[44:54])

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
        global input_count

        serial_port = str(self.com_combo.currentText())

        try:
            ser = serial.Serial( self.ports_dict[serial_port], 1152000)
        except serial.SerialException: 
            pass

        if input_count == 0:
            if ser.isOpen() == True:
                self.browser.append("<font color=red> Open  <b>%s</b> \
                    OK!</font>" % ser.portstr )
                self.uart_listen_thread.start()
                input_count = input_count + 1
        else:
            self.browser.append("<font color=red> Close <b>%s</b> \
                OK!</font>" % ser.portstr )
            input_count = 0
            ser.close()

    def exchange_file(self):
        #print "****"
        if self.filename != '':
            f = open(self.filename)  
            li = f.readlines()
            f.close() 
            #print type(li)
            id_data = str(self.dtq_id_lineedit.text())
            insert_data = "08FC0000" + id_data
            insert_data_hex = insert_data.decode("hex")

            check_sum = 0
            for i in insert_data_hex:
                check_sum = (ord(i) + check_sum) % 0x100
                print "%02X" % ord(i),
                print "check_sum = %02X" % check_sum

            print "check_sum = %02X" % (0x100-check_sum)
            insert_data = ':' + insert_data + "%02X\n" % (0x100-check_sum)
            li.insert(1, insert_data)
            #print li
            file_path = self.filename[0:len(self.filename)-4] 
            new_file_path = file_path + "_NEW.hex"
            new_file = open(new_file_path ,'w')  
            for i in li:
                new_file.write(i) 
            new_file.close()

            new_file = open(new_file_path)
            data = new_file.read()
            self.browser.setText(data)
            new_file.close()


    def band_start(self):
        global ser
        global input_count

        if ser.isOpen() == True:
            self.uart_listen_thread.start()
            cmd = "{'fun':'bind_start'}"
            ser.write(cmd)
            input_count = input_count + 1
            data = u"<b>S[%d]: </b>" % (input_count-1) + u"%s" % cmd
            self.uart_update_text(data)
            self.start_button.setText(u"关闭接收器")
        
    def choose_file(self):
        self.filename = QFileDialog.getOpenFileName(self, 'Open file', './')
        file = open(self.filename)
        data = file.read()
        self.browser.setText(data)
        file.close()
 
if __name__=='__main__':
    app = QApplication(sys.argv)
    datdebuger = QtqBurner()
    datdebuger.show()
    app.exec_()

