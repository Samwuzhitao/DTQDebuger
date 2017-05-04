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
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
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
        self.dtq_image_path = ''
        self.jsq_boot_path  = ''
        self.jsq_image_path = ''

        self.setWindowTitle(u"答题器烧录工具v0.1.0")

        self.com_combo=QComboBox(self) 
        self.com_combo.setFixedSize(75, 20)
        self.uart_scan()
        self.start_button= QPushButton(u"打开接收器")
        self.dtq_choose_image_button = QPushButton(u"答题器固件")
        self.save_button = QPushButton(u"转换文件")
        c_hbox = QHBoxLayout()
        c_hbox.addWidget(self.com_combo)
        c_hbox.addWidget(self.start_button)
        c_hbox.addWidget(self.dtq_choose_image_button)
        c_hbox.addWidget(self.save_button)

        self.dtq_id_label=QLabel(u"设备ID:") 
        self.dtq_id_lineedit = QLineEdit(u"11223344")
        self.time_label=QLabel(u"系统时间:") 
        self.time_lineedit = QLineEdit( time.strftime( 
            '%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

        e_hbox = QHBoxLayout()
        e_hbox.addWidget(self.dtq_id_label)
        e_hbox.addWidget(self.dtq_id_lineedit)
        e_hbox.addWidget(self.time_label)
        e_hbox.addWidget(self.time_lineedit)

        self.boot_button= QPushButton(u"BOOLLOADER")
        self.image_button = QPushButton(u"接收器固件")
        self.merge_button = QPushButton(u"合并2个文件")
        r_hbox = QHBoxLayout()
        r_hbox.addWidget(self.boot_button)
        r_hbox.addWidget(self.image_button)
        r_hbox.addWidget(self.merge_button)

        self.boot_browser = QTextBrowser()
        self.image_browser = QTextBrowser()
        i_hbox = QHBoxLayout()
        i_hbox.addWidget(self.boot_browser)
        i_hbox.addWidget(self.image_browser)

        self.browser = QTextBrowser()
        self.burn_button = QPushButton(u"烧录文件")
        vbox = QVBoxLayout()
        vbox.addWidget(self.browser)
        vbox.addLayout(r_hbox)
        vbox.addLayout(i_hbox)
        vbox.addWidget(self.burn_button)

        box = QVBoxLayout()
        box.addLayout(c_hbox)
        box.addLayout(e_hbox)
        
        box.addLayout(vbox)
        self.setLayout(box)
        self.resize( 600, 500 )

        self.dtq_choose_image_button.clicked.connect(self.choose_image_file)
        self.boot_button.clicked.connect(self.choose_image_file)
        self.image_button.clicked.connect(self.choose_image_file)
        self.merge_button.clicked.connect(self.merge_file)

        self.start_button.clicked.connect(self.band_start)
        self.save_button.clicked.connect(self.exchange_file)
        self.uart_listen_thread=UartListen()
        self.connect(self.uart_listen_thread,SIGNAL('output(QString)'),
            self.uart_update_text) 
        self.com_combo.currentIndexChanged.connect(self.change_uart)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def update_time(self):
        self.time_lineedit.setText(time.strftime( 
            '%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        #self.exchange_file()

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
            #id_data = "%08X" % string.atoi(data[44:54])
            id_data = "%08X" % string.atoi(str(data[44:54]))
            #string.atoi(str(self.dtq_id_lineedit.text()))
            self.dtq_id_lineedit.setText(id_data)
        self.exchange_file()

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
        if self.dtq_image_path != '':
            f = open(self.dtq_image_path)  
            li = f.readlines()
            f.close() 
            #print type(li)
            id_data = str(self.dtq_id_lineedit.text())
            #print id_data
            time_data = time.strftime( '%Y%m%d%H%M%S',time.localtime(time.time()))
            insert_data = "0BFC0000" + id_data + time_data 
            insert_data_hex = insert_data.decode("hex")

            check_sum = 0
            for i in insert_data_hex:
                check_sum = (ord(i) + check_sum) % 0x100

            insert_data = ':' + insert_data + "%02X\n" % (0x100-check_sum)
            li.insert(1, insert_data)
            #print li
            file_path = self.dtq_image_path[0:len(self.dtq_image_path)-4] 
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

    def choose_image_file(self):
        button = self.sender()

        if button is None or not isinstance(button, QPushButton):
            return
        #print "clicked button is %s " % button.text()
        button_str = button.text()

        if button_str == u"答题器固件":
            self.dtq_image_path = unicode(QFileDialog.getOpenFileName(self, 'Open file', './'))
            if len(self.dtq_image_path) > 0:
                f = open(self.dtq_image_path,"rb")
                data = f.read()
                self.browser.setText(data)
                f.close()
        if button_str == u"BOOLLOADER":
            self.jsq_boot_path = unicode(QFileDialog.getOpenFileName(self, 'Open file', './'))
            if len(self.jsq_boot_path) > 0:
                f = open(self.jsq_boot_path,"rb")
                data = f.read()
                self.boot_browser.setText(data)
                f.close()
        if button_str == u"接收器固件":
            self.jsq_image_path = unicode(QFileDialog.getOpenFileName(self, 'Open file', './'))
            if len(self.jsq_image_path) > 0:
                f = open(self.jsq_image_path,"rb")
                data = f.read()
                self.image_browser.setText(data)
                f.close()

    def merge_file(self):
        #print "****"
        if self.jsq_boot_path != '':
            f = open(self.jsq_boot_path)
            boot_li = f.readlines()
            f.close()

        if self.jsq_image_path != '':
            f = open(self.jsq_image_path)
            image_li = f.readlines()
            f.close()
            #print li
            file_path = self.jsq_image_path[0:len(self.jsq_image_path)-4] 
            new_file_path = file_path + "_BOOTLOADER.hex"

            new_file = open(new_file_path ,'w')  

            for i in range(0,len(boot_li)-1):
                new_file.write(boot_li[i]) 

            for i in image_li:
                new_file.write(i) 

            new_file.close()

            new_file = open(new_file_path)
            data = new_file.read()
            self.browser.setText(data)
            new_file.close()


if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = QtqBurner()
    datburner.show()
    app.exec_()

