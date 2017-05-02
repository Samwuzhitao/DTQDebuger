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
from ctypes import *
from math import *

from JsonDecode import *
from HexDecode  import *
from BinDecode  import *

ser              = 0
input_count      = 0
show_time_flag   = 0
decode_type_flag = 0
hex_decode_show_style = 1
down_load_image_flag  = 0

class UartListen(QThread): 
    def __init__(self,parent=None): 
        super(UartListen,self).__init__(parent) 
        self.working=True 
        self.num=0 
        self.hex_revice  = HexDecode()
        self.json_revice = JsonDecode()
        self.bin_decode = BinDecode()
        self.ReviceFunSets           = {
            0:self.uart_down_load_image_0,
            1:self.uart_down_load_image_1,
            2:self.uart_down_load_image_2,
            3:self.uart_down_load_image_3,
        }

    def __del__(self): 
        self.working=False 
        self.wait()

    def uart_down_load_image_0(self,read_char):
        global decode_type_flag
        global show_time_flag
        global down_load_image_flag

        recv_str      = ""
        ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'

        if decode_type_flag == 0:
            str1 = self.json_revice.r_machine(read_char)
        if decode_type_flag == 1:
            str1 = self.hex_revice.r_machine(read_char)
        if len(str1) != 0:
            now = time.strftime( ISOTIMEFORMAT,
                time.localtime(time.time()))
            if show_time_flag == 1:
                recv_str = u"[%s] <b>R[%d]: </b>" % (now, input_count-1) + u"%s" %  str1
            else:
                recv_str = u"<b>R[%d]: </b>" % (input_count-1) + u"%s" % str1
        return 0,recv_str

    def uart_down_load_image_1(self,read_char):
        global decode_type_flag
        global show_time_flag

        start_flag_count = 0
        recv_str = ""
        ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'
        retuen_flag = 1

        if decode_type_flag == 0:
            str1 = self.json_revice.r_machine(read_char)
        if decode_type_flag == 1:
            str1 = self.hex_revice.r_machine(read_char)
        if len(str1) != 0:
            sleep(2)
            now = time.strftime( ISOTIMEFORMAT,
                time.localtime(time.time()))
            if show_time_flag == 1:
                recv_str = u"[%s] <b>R[%d]: </b>" % (now, input_count-1) + u"%s" %  str1
            else:
                recv_str = u"<b>R[%d]: </b>" % (input_count-1) + u"%s" % str1

        if read_char == 'C':
            retuen_flag = 2
            recv_str = u"建立连接..."

        if read_char == '.':
            start_flag_count = start_flag_count + 1
            if start_flag_count == 3:
                recv_str = u"建立连接..."
                retuen_flag = 2
                start_flag_count = 0

        return retuen_flag,recv_str

    def uart_down_load_image_2(self,read_char):
        recv_str = ""
        recv_str = u"发送镜像文件信息..."
        data_path  = os.path.abspath("../") +'\\data\\'
        image_path = 'DTQ_RP551CPU_ZKXL0200_V0102.bin'
        size       = os.path.getsize(data_path+image_path)
        
        ack = '06'
        ack = ack.decode("hex")
        ser.write(ack)
        ser.write(self.bin_decode.encode_header_package(image_path,size))

        return 3,recv_str

    def uart_down_load_image_3(self,read_char):
        recv_str = ""
        if read_char == 'C':
            recv_str = u"接收校验通过..."
        return 0,recv_str

    def run(self): 
        global ser
        global down_load_image_flag

        while self.working==True: 
            if ser.isOpen() == True:
                read_char = ser.read(1)
                if down_load_image_flag >= 2:
                	print "status = %d char = %s " % (down_load_image_flag, read_char)
                next_flag,recv_str = self.ReviceFunSets[down_load_image_flag]( read_char )

                if len(recv_str) > 0:
                    if down_load_image_flag != 1:
                        self.emit(SIGNAL('output(QString)'),recv_str)
                        #print 'output(QString)',
                    else:
                        self.emit(SIGNAL('pressed_1_cmd(QString)'),recv_str )
                        #print 'pressed_1_cmd(QString)',
                    #print "status = %d char = %s str = %s" % (down_load_image_flag, read_char, recv_str)
                down_load_image_flag = next_flag

class DtqDebuger(QWidget):
    def __init__(self, parent=None):
        global ser

        super(DtqDebuger, self).__init__(parent)
        input_count = 0
        self.ports_dict = {}
        self.json_cmd_dict   = {}
        self.json_cmd_dict[u'清白名单'] = "{'fun':'clear_wl'}"
        self.json_cmd_dict[u'开启绑定'] = "{'fun':'bind_start'}"
        self.json_cmd_dict[u'停止绑定'] = "{'fun':'bind_stop'}"
        self.json_cmd_dict[u'设备信息'] = "{'fun':'get_device_info'}"
        self.json_cmd_dict[u'发送题目'] = "{'fun': 'answer_start','time': '2017-02-15:17:41:07:137',\
            'questions': [{'type': 's','id': '1','range': 'A-D'},\
            {'type': 'm','id': '13','range': 'A-F'},\
            {'type': 'j','id': '24','range': ''},\
            {'type': 'd','id': '27','range': '1-5'}]}"
        self.json_cmd_dict[u'查看配置'] ="{'fun':'check_config'}"
        self.json_cmd_dict[u'设置学号'] ="{'fun':'set_student_id','student_id':'1234'}"
        self.json_cmd_dict[u'设置信道'] ="{'fun': 'set_channel','tx_ch': '2','rx_ch': '6'}"
        self.json_cmd_dict[u'设置功率'] ="{'fun':'set_tx_power','tx_power':'5'}"
        self.json_cmd_dict[u'下载程序'] ="{'fun':'bootloader'}"
        self.json_cmd_dict[u'2.4g考勤'] ="{'fun':'24g_attendance','attendance_status': '1','attendance_tx_ch': '81'}"

        self.hex_cmd_dict   = {}
        self.hex_cmd_dict[u'清白名单'] = "5C 22 00 00 00 00 00 22 CA"
        self.hex_cmd_dict[u'开启绑定'] = "5C 41 00 00 00 00 01 01 41 CA"
        self.hex_cmd_dict[u'停止绑定'] = "5C 41 FF FF FF FF 01 00 40 CA"
        self.hex_cmd_dict[u'设备信息'] = "5C 2C 00 00 00 00 00 2C CA"
        self.hex_cmd_dict[u'单选题目'] = "5C 10 01 0C 14 55 0D 5A 00 00 00 00 00 11 03 01 01 7F 6D CA C1 CA"
        self.hex_cmd_dict[u'发送题目'] = "5C 28 00 00 00 00 14 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 1C CA"
        self.hex_cmd_dict[u'查看配置'] = u"暂无功能"
        self.hex_cmd_dict[u'设置学号'] = u"暂无功能"
        self.hex_cmd_dict[u'设置信道'] = u"暂无功能"
        self.hex_cmd_dict[u'设置功率'] = u"暂无功能"
        self.hex_cmd_dict[u'下载程序'] = u"暂无功能"
        self.hex_cmd_dict[u'2.4g考勤'] = u"暂无功能"

        self.open_com_button=QPushButton(u"打开串口")
        self.open_com_button.setFixedSize(75, 25)
        self.open_com_button.setStyleSheet(
            "QPushButton{border:1px solid lightgray;background:rgb(230,230,230)}"
            "QPushButton:hover{border-color:green;background:transparent}")  
        self.com_combo=QComboBox(self) 
        self.com_combo.setFixedSize(75, 20)
        self.uart_scan()

        self.baudrate_label=QLabel(u"波特率：") 
        self.baudrate_label.setFixedSize(60, 20)
        self.baudrate_lineedit = QLineEdit(u'1152000')
        self.baudrate_lineedit.setFixedSize(50, 20)
        self.baudrate_unit_label=QLabel(u"bps ") 
        self.baudrate_unit_label.setFixedSize(20, 20)

        self.displaystyle_label=QLabel(u"显示格式：")
        self.display_combo=QComboBox(self) 
        self.display_combo.addItem(u'16进制')
        self.display_combo.addItem(u'字符串')
        self.display_combo.setFixedSize(60, 20)
        self.display_combo.setCurrentIndex(self.display_combo.
            findText(u'字符串'))
        self.protocol_label=QLabel(u"协议版本：")
        self.protocol_combo=QComboBox(self) 
        self.protocol_combo.addItem(u'JSON')
        self.protocol_combo.addItem(u'HEX')
        self.protocol_combo.setFixedSize(60, 20)
        self.clear_revice_button=QPushButton(u"清空数据")
        self.clear_revice_button.setCheckable(False)
        self.clear_revice_button.setAutoExclusive(False)
        self.clear_revice_button.setFixedSize(75, 25)
        self.clear_revice_button.setStyleSheet(
            "QPushButton{border:1px solid lightgray;background:rgb(230,230,230)}"
            "QPushButton:hover{border-color:green;background:transparent}")

        self.send_cmd_combo=QComboBox(self) 
        self.send_cmd_combo.setFixedSize(75, 25)
        for key in self.json_cmd_dict:
            self.send_cmd_combo.addItem(key)
        self.send_cmd_combo.setCurrentIndex(self.send_cmd_combo.
            findText(u'设备信息'))
        self.browser = QTextBrowser()
        self.auto_send_chackbox = QCheckBox(u"自动发送") 
        self.com_combo.setFixedSize(75, 25)
        self.show_time_chackbox = QCheckBox(u"显示时间")
        self.com_combo.setFixedSize(75, 25) 
        self.browser.setFont(QFont("Courier New", 8, False))

        self.send_time_label=QLabel(u"发送周期：") 
        self.send_time_label.setFixedSize(60, 20)
        self.send_time_lineedit = QLineEdit(u'4000')
        self.send_time_lineedit.setFixedSize(50, 20)
        self.send_time_unit_label=QLabel(u"ms ") 
        self.send_time_unit_label.setFixedSize(20, 20)

        self.update_fm_button=QPushButton(u"升级程序")
        self.update_fm_button.setCheckable(False)
        self.update_fm_button.setAutoExclusive(False)
        self.update_fm_button.setFixedSize(75, 25)
        self.update_fm_button.setStyleSheet(
            "QPushButton{border:1px solid lightgray;background:rgb(230,230,230)}"
            "QPushButton:hover{border-color:green;background:transparent}")

        self.send_lineedit = QLineEdit(u"修改或者输入指令，按Enter键发送！")
        self.send_lineedit.selectAll()
        self.send_lineedit.setDragEnabled(True)
        self.send_lineedit.setMaxLength(5000)

        str = QStringList(["{'fun':'clear_wl'}",
                           "{'fun':'bind_start'}",
                           "{'fun':'bind_stop'}",
                           "{'fun':'get_device_info'}",
                           "{'fun':'check_config'}",
                           "{'fun':'set_student_id','student_id':'1234'}",
                           "{'fun':'set_channel','tx_ch':'2','rx_ch':'6'}",
                           "{'fun':'set_tx_power','tx_power':'5'}",
                           "{'fun':'bootloader'}"
                           "{'fun':'24g_attendance','attendance_status':'1','attendance_tx_ch':'81'}"
                           ])#预先设置字典  
        self.send_lineedit.setCompleter(QCompleter(str)) #将字典添加到lineEdit中  

        c_hbox = QHBoxLayout()
        c_hbox.addWidget(self.com_combo)
        c_hbox.addWidget(self.open_com_button)
        c_hbox.addWidget(self.baudrate_label)
        c_hbox.addWidget(self.baudrate_lineedit)
        c_hbox.addWidget(self.baudrate_unit_label)
        c_hbox.addWidget(self.displaystyle_label)
        c_hbox.addWidget(self.display_combo)
        c_hbox.addWidget(self.clear_revice_button)

        t_hbox = QHBoxLayout()
        t_hbox.addWidget(self.show_time_chackbox)
        t_hbox.addWidget(self.auto_send_chackbox)
        t_hbox.addWidget(self.send_time_label)
        t_hbox.addWidget(self.send_time_lineedit)
        t_hbox.addWidget(self.send_time_unit_label)
        t_hbox.addWidget(self.protocol_label)
        t_hbox.addWidget(self.protocol_combo)
        t_hbox.addWidget(self.update_fm_button)

        d_hbox = QHBoxLayout()
        d_hbox.addWidget(self.send_cmd_combo)
        d_hbox.addWidget(self.send_lineedit)

        vbox = QVBoxLayout()
        vbox.addLayout(c_hbox)
        vbox.addLayout(t_hbox)
        vbox.addWidget(self.browser)
        vbox.addLayout(d_hbox)
        self.setLayout(vbox)

        self.setGeometry(500, 80, 555, 730)
        self.send_lineedit.setFocus()
        self.send_lineedit.setFont(QFont("Courier New", 8, False))

        self.open_com_button.clicked.connect(self.open_uart)
        self.send_lineedit.returnPressed.connect(self.uart_send_data)
        self.clear_revice_button.clicked.connect(self.uart_data_clear)
        self.show_time_chackbox.stateChanged.connect(self.uart_show_time_check)
        self.auto_send_chackbox.stateChanged.connect(self.uart_auto_send_check)

        self.send_cmd_combo.currentIndexChanged.connect(self.update_uart_protocol)
        self.protocol_combo.currentIndexChanged.connect(self.update_uart_protocol)
        self.display_combo.currentIndexChanged.connect(self.update_uart_hex_decode_show_style)

        self.com_combo.currentIndexChanged.connect(self.change_uart)
        self.com_combo.currentIndexChanged.connect(self.update_uart_protocol)

        self.update_fm_button.clicked.connect(self.uart_download_image)
        self.update_fm_button.clicked.connect(self.update_uart_protocol)
        self.update_fm_button.clicked.connect(self.uart_send_data)

        self.setWindowTitle(u"答题器调试工具v0.1.2")

        self.uart_listen_thread=UartListen()
        self.connect(self.uart_listen_thread,SIGNAL('output(QString)'),
            self.uart_update_text) 
        self.connect(self.uart_listen_thread,SIGNAL('pressed_1_cmd(QString)'),
            self.uart_send_press_1_text) 
        self.timer = QTimer()
        self.timer.timeout.connect(self.uart_send_data)

    def open_uart(self):
        global ser
        global decode_type_flag
        global input_count

        serial_port = str(self.com_combo.currentText())
        baud_rate   = str(self.baudrate_lineedit.text())

        try:
            ser = serial.Serial( self.ports_dict[serial_port], 
                string.atoi(baud_rate, 10))
        except serial.SerialException: 
            pass

        if input_count == 0:
            if ser.isOpen() == True:
                self.browser.append("<font color=red> Open  <b>%s</b> \
                    OK!</font>" % ser.portstr )
                self.open_com_button.setText(u"关闭串口")
                input_count = input_count + 1
        else:
            self.browser.append("<font color=red> Close <b>%s</b> \
                OK!</font>" % ser.portstr )
            self.open_com_button.setText(u"打开串口")
            input_count = 0
            ser.close()

    def uart_send_press_1_text(self,data):
        global ser
        global down_load_image_flag

        if down_load_image_flag == 1:
            self.browser.append(data)
            self.send_lineedit.setText("1:Download Image...")
            self.timer.stop()
            self.timer.start(300)

        if down_load_image_flag == 2:
            if data == u'JSON':
                decode_type_flag = 0
                data = unicode(self.send_cmd_combo.currentText())
                self.send_lineedit.setText(self.json_cmd_dict[data])
      
            if data == u'HEX':
                decode_type_flag = 1
                data = unicode(self.send_cmd_combo.currentText())
                self.send_lineedit.setText(self.hex_cmd_dict[data])
            self.timer.stop()

    def change_uart(self):
        global input_count
        global ser

        if ser != 0:
            input_count = 0
            ser.close()

    def update_uart_hex_decode_show_style(self):
        global hex_decode_show_style
        data = unicode(self.display_combo.currentText())
        if data == u'16进制':
            hex_decode_show_style = 0
        if data == u'字符串':
            hex_decode_show_style = 1

    def update_uart_protocol(self):
        global decode_type_flag

        data = unicode(self.protocol_combo.currentText())
        if data == u'JSON':
            decode_type_flag = 0
            data = unicode(self.send_cmd_combo.currentText())
            self.send_lineedit.setText(self.json_cmd_dict[data])
  
        if data == u'HEX':
            decode_type_flag = 1
            data = unicode(self.send_cmd_combo.currentText())
            self.send_lineedit.setText(self.hex_cmd_dict[data])
        #print decode_type_flag

    def uart_download_image(self):
        global down_load_image_flag

        self.send_cmd_combo.setCurrentIndex(self.send_cmd_combo.
            findText(u'下载程序'))
        down_load_image_flag = 1

    def uart_show_time_check(self):
        global show_time_flag
        if self.show_time_chackbox.isChecked():
            show_time_flag = 1
        else:
            show_time_flag = 0

    def uart_auto_send_check(self):  
        atuo_send_time = string.atoi(str(self.send_time_lineedit.text()))

        if self.auto_send_chackbox.isChecked():
            self.timer.start(atuo_send_time)
        else:
            self.timer.stop()

    def uart_update_text(self,data):
        self.browser.append(data)

    def uart_data_clear(self):
        self.browser.clear()

    def uart_scan(self):
        for i in range(256):
            
            try:
                s = serial.Serial(i)
                self.com_combo.addItem(s.portstr)
                self.ports_dict[s.portstr] = i
                s.close()
            except serial.SerialException:
                pass

    def uart_send_data(self):
        global ser
        global input_count
        global show_time_flag
        global decode_type_flag

        serial_port = str(self.com_combo.currentText())
        baud_rate   = str(self.baudrate_lineedit.text())
        ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'
        now = time.strftime( ISOTIMEFORMAT, time.localtime( time.time() ) )

        if input_count == 0:
            try:
                ser = serial.Serial( self.ports_dict[serial_port], 
                    string.atoi(baud_rate, 10))
            except serial.SerialException: 
                pass
            
            if ser.isOpen() == True:
                self.browser.append("<font color=red> Open <b>%s</b> \
                    OK!</font>" % ser.portstr )
                self.open_com_button.setText(u"关闭串口")
                self.uart_listen_thread.start()

                data = str(self.send_lineedit.text())
                if show_time_flag == 1:
                   self.browser.append(u"【%s】 <b>S[%d]:</b> %s"
                    % (now, input_count,data))
                else:
                    self.browser.append(u"<b>S[%d]:</b> %s" %(input_count, data))
                input_count = input_count + 1

                if  decode_type_flag == 1:
                    data = data.replace(' ','')
                    data = data.decode("hex")
                    #print data
                ser.write(data)
            else:
                self.browser.append("<font color=red> Open <b>%s</b> \
                    Error!</font>" % ser.portstr )
                self.open_com_button.setText(u"关闭串口")
        else:
            if ser.isOpen() == True:
                data = str(self.send_lineedit.text())
                if show_time_flag == 1:
                    self.browser.append(u"[%s] <b>S[%d]:</b> %s" 
                        % (now, input_count, data))
                else:
                    self.browser.append(u"<b>S[%d]:</b> %s" %(input_count, data))
                input_count = input_count + 1

                if  decode_type_flag == 1:
                    data = data.replace(' ','')
                    data = data.decode("hex")
                    #print data
                ser.write(data)
            else:
                self.browser.append("<font color=red> Open <b>%s</b> \
                    Error!</font>" % ser.portstr )
                self.open_com_button.setText(u"关闭串口")

if __name__=='__main__':
    app = QApplication(sys.argv)
    datdebuger = DtqDebuger()
    datdebuger.show()
    app.exec_()

