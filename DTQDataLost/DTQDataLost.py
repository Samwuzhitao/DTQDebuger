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

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as figureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

ser              = ''
input_count      = 0
temp_count       = 0

class Mytimer():
    """docstring for ClassName"""
    def __init__(self): 
        self.s    = 0
        self.min  = 0
        self.hour = 0
        self.date = 0
        self.mon  = 0
        self.year = 0

    def inc(self):
        self.s = self.s + 1
        if self.s == 60:
            self.s = 0
            self.min = self.min + 1
            if self.min == 60:
                self.min = 0
                self.hour = self.hour + 1
                if self.hour == 24:
                    self.hour = 0
                    self.date = self.date + 1

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
        super(QtqBurner, self).__init__(parent)
        self.ports_dict = {}
        self.x = []
        self.y = []
        self.start_time = int(time.time())
        self.setWindowTitle(u"答题器丢包测试工具v0.1.0")
        self.com_combo=QComboBox(self) 
        self.com_combo.setFixedSize(75, 20)
        self.uart_scan()
        self.start_button= QPushButton(u"打开接收器")
        self.dtq_id_label=QLabel(u"发送周期:") 
        self.dtq_id_lineedit = QLineEdit(u"10000")
        self.time_label=QLabel(u"系统时间:") 
        self.time_lineedit = QLineEdit( time.strftime( 
            '%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        e_hbox = QHBoxLayout()
        e_hbox.addWidget(self.com_combo)
        e_hbox.addWidget(self.start_button)
        e_hbox.addWidget(self.dtq_id_label)
        e_hbox.addWidget(self.dtq_id_lineedit)
        e_hbox.addWidget(self.time_label)
        e_hbox.addWidget(self.time_lineedit)
        
        #返回当前的figure
        self.figure = plt.gcf() 
        self.canvas = figureCanvas(self.figure)
        plt.title('The answer is packet loss rate statistics histogram')
        plt.xlabel('UID POS')
        plt.ylabel('answer count')

        self.burn_button = QPushButton(u"开始测试")
        self.burn_button.setFont(QFont("Courier New", 14, QFont.Bold))
        self.burn_button.setFixedHeight( 40 )
        self.burn_button.setStyleSheet(
            "QPushButton{border:1px solid lightgray;background:rgb(230,230,230)}"
            "QPushButton:hover{border-color:green;background:transparent}")
        box = QVBoxLayout()
        box.addLayout(e_hbox)
        box.addWidget(self.canvas)
        box.addWidget(self.burn_button)
        self.setLayout(box)
        self.resize( 540, 500 )

        self.start_button.clicked.connect(self.band_start)
        self.burn_button.clicked.connect(self.time_start)
        self.uart_listen_thread=UartListen()
        self.connect(self.uart_listen_thread,SIGNAL('output(QString)'),
            self.uart_update_text) 
        self.com_combo.currentIndexChanged.connect(self.change_uart)

        self.timer = QTimer()
        self.my_timer = Mytimer()
        self.timer.timeout.connect(self.update_time)

    def time_start(self):
        self.timer.start(1000)

        button = self.sender()

        if button is None or not isinstance(button, QPushButton):
            return
        #print "clicked button is %s " % button.text()
        button_str = button.text()

        if button_str == u"开始测试":
            self.time_label.setText(u"测试时间:") 
            self.burn_button.setText(u"停止测试")
        else:
            self.time_label.setText(u"测试时间:") 
            self.burn_button.setText(u"开始测试")
            self.timer.stop()
            if ser != '':
                input_count = 0
                ser.close()


    def update_time(self):
        global temp_count

        temp_count = temp_count + 1
        self.my_timer.inc()
        self.time_lineedit.setText(
            '%02d %02d:%02d:%02d' % (self.my_timer.date, self.my_timer.hour, 
            self.my_timer.min, self.my_timer.s))
        self.x.append(temp_count)
        self.y.append(temp_count)
        plt.bar(self.x,self.y)
        self.canvas.draw()

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
        print data[34:41]
        if data[34:41] == "card_id":
            id_data = "%08X" % string.atoi(str(data[44:54]))
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
        if serial_port != '':
            try:
                ser = serial.Serial( self.ports_dict[serial_port], 1152000)
            except serial.SerialException: 
                return
        else:
            self.browser.append(u"<b>Error[%d]:</b> 未检测到设备，请插入设备！" 
                % input_count)
            return 

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

    def band_start(self):
        global ser
        global input_count

        self.open_uart()
        if ser != '':
            if ser.isOpen() == True:
                self.uart_listen_thread.start()
                cmd = "{'fun':'bind_start'}"
                ser.write(cmd)
                input_count = input_count + 1
                data = u"<b>S[%d]: </b>" % (input_count-1) + u"%s" % cmd
                self.uart_update_text(data)
                self.start_button.setText(u"关闭接收器")

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = QtqBurner()
    datburner.show()
    app.exec_()

