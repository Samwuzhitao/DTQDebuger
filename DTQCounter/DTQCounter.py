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
from DTQMonitor import *

ser              = ''
input_count      = 0
temp_count       = 0
TIMER_STR_LEN    = 22
FUN_STR_ADDRESS  = 21
ISOTIMEFORMAT    = '%Y-%m-%d %H:%M:%S'

answer_40_start_cmd = "{'fun': 'answer_start','time': '2017-02-15:17:41:07:137',\
                                'raise_hand': '1',\
                                'attendance': '1',\
                                'questions': [\
                                {'type': 's','id': '54','range': 'A-D'},\
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



class UartListen(QThread):
    def __init__(self,com,parent=None):
        super(UartListen,self).__init__(parent)
        self.working  = True
        self.com      = com
        self.rcmd     = JsonDecode()
        self.data_buffer  = {}
        self.buffer_index = 0

    def __del__(self):
        self.working=False
        self.wait()

    def run(self):
        while self.working==True:
            if self.com.isOpen() == True:
                try:
                    read_char = self.com.read(1)
                    recv_str  = self.rcmd.r_machine(read_char)
                except serial.SerialException:
                     self.working = False
                     pass
                except AttributeError :
                    pass
                if recv_str :
                    self.data_buffer[self.buffer_index] = recv_str
                    self.emit(SIGNAL('r_machine_output(int)' ),self.buffer_index )
                    print 'send_bufeer : %d ' % self.buffer_index
                    self.buffer_index = (self.buffer_index + 1) % 3

class DtqCounter(QWidget):
    def __init__(self, parent=None):
        super(DtqCounter, self).__init__(parent)
        self.dtq_monitor = DTQMonitor()
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
        self.cmd_combo.addItems(['80','60','40'])
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
        self.result_browser = QTextBrowser ()
        self.result_browser.setFixedHeight(100)
        box = QVBoxLayout()
        box.addLayout(e_hbox)
        box.addWidget(self.result_browser)
        box.addWidget(self.burn_button)
        box.addWidget(self.browser)
        self.setLayout(box)
        self.resize( 750, 600 )

        self.start_button.clicked.connect(self.band_start)
        self.clear_revice_button.clicked.connect(self.uart_data_clear)
        self.burn_button.clicked.connect(self.time_start)
        self.cmd_combo.currentIndexChanged.connect(self.cmd_hange)

    def cmd_hange(self):
        cmd_str = unicode(self.cmd_combo.currentText())
        self.cmd = self.answer_cmd_dict[cmd_str]

    def uart_data_clear(self):
        self.browser.clear()

    def time_start(self):
        button = self.sender()

        if button is None or not isinstance(button, QPushButton):
            return
        button_str = button.text()

        if button_str == u"开始自动发送测试":
            self.time_label.setText(u"测试时间:")
            self.burn_button.setText(u"停止自动发送测试")
            self.start_time = int(time.time())
            if self.uart_thread.com :
                if self.uart_thread.com.isOpen() == True:
                    self.uart_thread.com.write(self.cmd)
            if self.dtq_monitor.holk_fun == None:
                self.dtq_monitor.config_data_update(self.browser.append)
        else:
            self.time_label.setText(u"测试时间:")
            self.burn_button.setText(u"开始自动发送测试")
            for id_data in self.uid_list:
                self.data_dict[id_data] = 0

            for item in self.dtq_monitor.ser_list:
                self.dtq_monitor.monitor_dict[item].quit()
                self.dtq_monitor.monitor_dict[item].com.close()

    def uart_update_text(self,buffer_index):
        print 'revice_bufeer : %d ' % buffer_index
        json_data = self.uart_thread.data_buffer[buffer_index]
        data = json_data.replace('\'','\"')

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

            if fun == "bind_stop":
                self.start_button.setText(u"打开接收器")
                self.uart_thread.com.close()

            if fun == "get_device_info":
                print data
                self.start_button.setText(u"关闭接收器")
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
                        data_str = ''
                        i = 0
                        for item in self.uid_list:
                            if self.data_dict[item] != 0:
                                uid_hex = string.atoi(item,10)
                                uid_hex = ((uid_hex & 0xff00ff00) >>  8)|((uid_hex & 0x00ff00ff) <<  8)
                                uid_hex = ((uid_hex & 0xffff0000) >> 16)|((uid_hex & 0x0000ffff) << 16)
                                i = i + 1
                                if (i % 6) == 0:
                                    data_str = data_str + "[ %08X:%6d ] \r\n" % (uid_hex,self.data_dict[item])
                                else:
                                    data_str = data_str + "[ %08X:%6d ] " % (uid_hex,self.data_dict[item])

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
        serial_port = str(self.com_combo.currentText())
        if serial_port != '':
            try:
                ser = serial.Serial( self.ports_dict[serial_port], 1152000)
            except serial.SerialException:
                return
        else:
            self.browser.append(u"Error: 未检测到设备，请插入设备！")
            return

        return ser

    def band_start(self):
        button = self.sender()

        if button is None or not isinstance(button, QPushButton):
            return
        button_str = button.text()

        if button_str == u"打开接收器":
            serport = self.open_uart()
            if serport :
                self.uart_thread = UartListen(serport)
                self.connect(self.uart_thread,SIGNAL('r_cmd_message(QString, QString)'),self.uart_update_text)
                self.uart_thread.start()
                cmd = "{'fun':'get_device_info'}"
                self.uart_thread.com.write(cmd)
                self.browser.append(u"S:%s" % cmd)

        else:
            cmd = "{'fun':'bind_stop'}"
            self.browser.append(u"S:%s" % cmd)
            if self.uart_thread.com:
                if self.uart_thread.com.isOpen() == True:
                    self.uart_thread.com.write(cmd)

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = DtqCounter()
    datburner.show()
    app.exec_()

