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
import json
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from JsonDecode import *

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as figureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from pylab import *
#指定默认字体
mpl.rcParams['font.sans-serif'] = ['SimHei']
#解决保存图像是负号'-'显示为方块的问题
mpl.rcParams['axes.unicode_minus'] = False

ser              = ''
input_count      = 0
temp_count       = 0
TIMER_STR_LEN    = 22
FUN_STR_ADDRESS  = 21
ISOTIMEFORMAT    = '%Y-%m-%d %H:%M:%S'
start_test_flag  = 0

answer_40_start_cmd = "{'fun': 'answer_start','time': '2017-02-15:17:41:07:137',\
                                'raise_hand': '1',\
                                'attendance': '1',\
                                'questions': [\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '10','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '20','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '30','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '40','range': 'A-F'}\
                                ]}"

answer_60_start_cmd = "{'fun': 'answer_start','time': '2017-02-15:17:41:07:137',\
                                'raise_hand': '1',\
                                'attendance': '1',\
                                'questions': [\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '10','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '20','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '30','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '40','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '50','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '60','range': 'A-F'}\
                                ]}"

answer_80_start_cmd = "{'fun': 'answer_start','time': '2017-02-15:17:41:07:137',\
                                'raise_hand': '1',\
                                'attendance': '1',\
                                'questions': [\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '10','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '20','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '30','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '40','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '50','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '60','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '9','range': 'A-D'},\
                                {'type': 'm','id': '70','range': 'A-F'},\
                                {'type': 's','id': '1','range': 'A-D'},\
                                {'type': 'm','id': '2','range': 'A-F'},\
                                {'type': 'j','id': '3','range': ''},\
                                {'type': 'd','id': '4','range': '1-5'},\
                                {'type': 's','id': '5','range': 'A-D'},\
                                {'type': 'm','id': '6','range': 'A-F'},\
                                {'type': 'j','id': '7','range': ''},\
                                {'type': 'd','id': '8','range': '1-5'},\
                                {'type': 's','id': '79','range': 'A-D'},\
                                {'type': 'g','id': '80','range': ''}\
                                ]}"

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
        self.ReviceFunSets = { 0:self.uart_down_load_image_0 }

    def __del__(self):
        self.working=False
        self.wait()

    def uart_down_load_image_0(self,read_char):
        str1 = self.json_revice.r_machine(read_char)

        if str1:
            now = time.strftime( ISOTIMEFORMAT,
                time.localtime(time.time()))
            return str1

    def run(self):
        global ser

        while self.working==True:
            if ser.isOpen() == True:
                # try:
                read_char = ser.read(1)
                # except SerialException:
                    # pass
                recv_str = self.ReviceFunSets[0]( read_char )
                if recv_str:
                    self.emit(SIGNAL('output(QString)'),recv_str)

class DtqCounter(QWidget):
    def __init__(self, parent=None):
        super(DtqCounter, self).__init__(parent)
        self.ports_dict = {}
        self.data_dict  = {}
        self.uid_list   = []
        self.answer_cmd_dict = {
              u'40':answer_40_start_cmd,
              u'60':answer_60_start_cmd,
              u'80':answer_80_start_cmd }
        self.cmd = answer_40_start_cmd
        self.start_time = 0
        self.setWindowTitle(u"答题器丢包测试工具v0.1.0")
        self.com_combo=QComboBox(self)
        self.com_combo.setFixedSize(75, 20)
        self.cmd_combo=QComboBox(self)
        self.cmd_combo.addItems(['40','60','80'])
        self.uart_scan()
        self.start_button= QPushButton(u"打开接收器")
        self.dtq_id_label=QLabel(u"uID:")
        self.dtq_id_lineedit = QLineEdit(u"1234567890")
        self.dtq_id_lineedit.setFixedSize(70, 20)
        self.time_label=QLabel(u"时间:")
        self.time_lineedit = QLineEdit( time.strftime(
            '%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        self.clear_revice_button=QPushButton(u"清空数据")
        e_hbox = QHBoxLayout()
        e_hbox.addWidget(self.com_combo)
        e_hbox.addWidget(self.start_button)
        e_hbox.addWidget(self.dtq_id_label)
        e_hbox.addWidget(self.dtq_id_lineedit)
        e_hbox.addWidget(self.time_label)
        e_hbox.addWidget(self.time_lineedit)
        e_hbox.addWidget(self.cmd_combo)
        e_hbox.addWidget(self.clear_revice_button)

        self.burn_button = QPushButton(u"开始自动发送测试")
        self.burn_button.setFont(QFont("Courier New", 14, QFont.Bold))
        self.burn_button.setFixedHeight( 40 )
        self.burn_button.setStyleSheet(
            "QPushButton{border:1px solid lightgray;background:rgb(230,230,230)}"
            "QPushButton:hover{border-color:green;background:transparent}")
        self.browser = QTextBrowser ()
        self.browser.setFixedHeight(200)
        self.result_browser = QTextBrowser ()
        box = QVBoxLayout()
        box.addLayout(e_hbox)
        box.addWidget(self.result_browser)
        box.addWidget(self.burn_button)
        box.addWidget(self.browser)
        self.setLayout(box)
        self.resize( 600, 600 )

        self.start_button.clicked.connect(self.band_start)
        self.clear_revice_button.clicked.connect(self.uart_data_clear)
        self.burn_button.clicked.connect(self.time_start)
        self.uart_listen_thread=UartListen()
        self.connect(self.uart_listen_thread,SIGNAL('output(QString)'),
            self.uart_update_text)
        self.com_combo.currentIndexChanged.connect(self.change_uart)
        self.cmd_combo.currentIndexChanged.connect(self.cmd_hange)
        self.timer = QTimer()
        self.my_timer = Mytimer()

    def cmd_hange(self):
        cmd_str = unicode(self.cmd_combo.currentText())
        self.cmd = self.answer_cmd_dict[cmd_str]

    def uart_data_clear(self):
        self.browser.clear()

    def time_start(self):
        global start_test_flag
        global input_count
        global ser
        button = self.sender()

        if button is None or not isinstance(button, QPushButton):
            return
        button_str = button.text()

        if button_str == u"开始自动发送测试":
            self.time_label.setText(u"测试时间:")
            self.burn_button.setText(u"停止自动发送测试")
            start_test_flag = 1
            self.start_time = int(time.time())
            if ser != '':
                if input_count == 0:
                    self.open_uart()
                if ser.isOpen() == True:
                    ser.write(self.cmd)
        else:
            self.time_label.setText(u"测试时间:")
            self.burn_button.setText(u"开始自动发送测试")
            for id_data in self.uid_list:
                self.data_dict[id_data] = 0

            if ser != '':
                input_count = 0
                ser.close()

    def change_uart(self):
        global input_count
        global ser

        if ser != 0:
            input_count = 0
            ser.close()
        if input_count == 0:
            self.open_uart()

    def update_time(self):
        global temp_count
        global input_count
        global ser
        global start_test_flag

        temp_count = temp_count + 1

        if start_test_flag == 0:
            now = time.strftime( ISOTIMEFORMAT, time.localtime(time.time()))
            self.time_lineedit.setText(now)
        else:
            self.my_timer.inc()
            self.time_lineedit.setText(
                '%02d.%02d %02d:%02d:%02d' % (self.my_timer.mon,self.my_timer.date,
                 self.my_timer.hour, self.my_timer.min, self.my_timer.s))

            if temp_count % 5 == 0:
                if ser != '':
                    if ser.isOpen() == True:
                        now = time.strftime( ISOTIMEFORMAT, time.localtime(time.time()))
                        ser.write(self.cmd)
                        self.browser.setText(u"【%s】<b>S[%d]:</b> %s" %(now,input_count, self.cmd))
                        input_count = input_count + 1

    def autolabel(self,rects):
        for rect in rects:
            height = rect.get_height()
            plt.text(rect.get_x()+rect.get_width()/2, height, u'%s' % int(height))

    def uart_update_text(self,data):
        data = data.replace('\'','\"')

        json_dict = {}
        try:
            json_dict = json.loads(str(data))
        except ValueError:
            pass
            return

        if json_dict.has_key(u"fun") == True:
            fun = json_dict[u"fun"]
            if fun == "update_card_info":
                if json_dict.has_key(u"card_id") == True:
                    id_data = json_dict[u"card_id"]
                    self.dtq_id_lineedit.setText(id_data)
                    if id_data not in self.uid_list:
                        self.data_dict[id_data] = 0
                        self.uid_list.append(id_data)
                        self.browser.append(data)
                        print self.uid_list

            if fun == "get_device_info":
                if json_dict.has_key(u"list") == True:
                    list_str = json_dict[u"list"]
                    if list_str:
                        for item in list_str:
                            uid = item[u"uid"]
                            if uid not in self.uid_list:
                                self.data_dict[uid] = 0
                                self.uid_list.append(uid)
                        uid_str = str(self.uid_list)
                        self.browser.append(uid_str)

            if fun == "update_answer_list":
                if json_dict.has_key(u"card_id") == True:
                    id_data = json_dict[u"card_id"]
                    if id_data in self.uid_list:
                        self.data_dict[id_data] = self.data_dict[id_data] + 1
                        # data = str(self.data_dict)
                        data_str = ''
                        i = 0
                        for item in self.uid_list:
                            if self.data_dict[item] != 0:
                                i = i + 1
                                if (i % 4) == 0:
                                    data_str = data_str + " [ %10s:%6d ]\r\n" % (item,self.data_dict[item])
                                else:
                                    data_str = data_str + " [ %10s:%6d ]" % (item,self.data_dict[item])

                        self.result_browser.setText(data_str)

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

    def band_start(self):
        global ser
        global input_count

        button = self.sender()

        if button is None or not isinstance(button, QPushButton):
            return
        button_str = button.text()

        if button_str == u"打开接收器":
            self.open_uart()
            if ser != '':
                if ser.isOpen() == True:
                    self.uart_listen_thread.start()
                    cmd = "{'fun':'get_device_info'}"
                    ser.write(cmd)
                    self.browser.append(u"<b>S[%d]:</b> %s" %(input_count, cmd))
                    input_count = input_count + 1
                    # cmd = "{'fun':'bind_start'}"
                    # ser.write(cmd)
                    # self.browser.append(u"<b>S[%d]:</b> %s" %(input_count, cmd))
                    # input_count = input_count + 1
                    self.start_button.setText(u"关闭接收器")
        else:
            if ser != '':
                input_count = 0
                cmd = "{'fun':'bind_stop'}"
                if ser != '':
                    if ser.isOpen() == True:
                        ser.write(cmd)
                        ser.close()
            self.start_button.setText(u"打开接收器")

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = DtqCounter()
    datburner.show()
    app.exec_()

