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
import logging
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
image_path            = ''

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = 'log.txt',
    filemode = 'w',
    format = u'【%(asctime)s】 %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
)

class UartListen(QThread): 
    def __init__(self,parent=None): 
        super(UartListen,self).__init__(parent) 
        self.working  = True 
        self.num      = 0 
        self.info_str = ''
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
        global hex_decode_show_style

        recv_str      = ""
        ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'

        if decode_type_flag == 0:
            str1 = self.json_revice.r_machine(read_char)
        if decode_type_flag == 1:
            self.hex_revice.show_style = hex_decode_show_style
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
        recv_str    = ""
        retuen_flag = 1

        char = "%02X" % ord(read_char)
        self.info_str += read_char
        if char == '0A':
            recv_str = self.info_str
            self.info_str = ''
  
        if char == '43':
            retuen_flag = 2
            recv_str = u"STEP[1]:建立连接成功..."

        return retuen_flag,recv_str

    def uart_down_load_image_2(self,read_char):
    	global ser
    	global image_path

        recv_str = ""
        retuen_flag = 2

        if read_char == 'C':
            recv_str = u"STEP[2]:发送镜像信息..."

            ack = '06'
            ack = ack.decode("hex")
            ser.write(ack)
            ser.write(self.bin_decode.soh_pac(image_path))
            retuen_flag = 3

        return retuen_flag,recv_str

    def uart_down_load_image_3(self,read_char):
        global down_load_image_flag
        recv_str = ""
        retuen_flag = 3

        char = "%02X" % ord(read_char)
        if self.bin_decode.over == 3:
            self.info_str += read_char
            #print self.info_str 
            if char == '0A':
                #print self.info_str 
                recv_str = self.info_str
                self.info_str = ''
                if recv_str[0:5] == 'Start':
                    retuen_flag = 0
                    self.bin_decode.clear() 

        #print "%s self.bin_decode.over = %d" % (char,self.bin_decode.over)
        if char == '06':
            revice_rate = self.bin_decode.send_index*100.0 / self.bin_decode.file_size
            temp_str = int(revice_rate / 2.5)*'#' + (40-int(revice_rate / 2.5))*' '

            recv_str = u"STEP[3]:传输镜像文件：%s %3d%%" % (temp_str,revice_rate)
   
            if self.bin_decode.over == 0:
                ser.write(self.bin_decode.stx_pac())

            if self.bin_decode.over == 1:
                eot = '04'
                #print eot
                eot = eot.decode("hex")
                ser.write(eot)
                self.bin_decode.over = 2

        if char == '43':
            #recv_str = u"reviceed CRC..."
            if self.bin_decode.over >= 2:    
                ser.write(self.bin_decode.soh_pac_empty())
                self.bin_decode.over = 3
               
        if char == '15':
            recv_str = u"接收到 NACK..."

        if char == '18':
            recv_str = u"接收到 CA..."


        return retuen_flag,recv_str

    def run(self): 
        global ser
        global down_load_image_flag

        while self.working==True: 
            if ser.isOpen() == True:
                read_char = ser.read(1)

                #print "status = %d char = %02X " % (down_load_image_flag, ord(read_char))
                next_flag,recv_str = self.ReviceFunSets[down_load_image_flag]( read_char )

                if len(recv_str) > 0:
                    if down_load_image_flag != 1:
                        self.emit(SIGNAL('protocol_message(QString)'),recv_str)
                        #print 'protocol_message(QString)',
                    else:
                        self.emit(SIGNAL('download_image_info(QString)'),recv_str )
                    #print "status = %d char = %s str = %s" % (down_load_image_flag, read_char, recv_str)
                down_load_image_flag = next_flag

class DtqDebuger(QWidget):
    def __init__(self, parent=None):
        global ser

        super(DtqDebuger, self).__init__(parent)
        input_count        = 0
        self.ports_dict    = {}
        self.json_cmd_dict = {}
        self.process_bar   = 0
        self.cmd_file_name = ''
        self.json_cmd_dict[u'清白名单'] = "{'fun':'clear_wl'}"
        self.json_cmd_dict[u'开启绑定'] = "{'fun':'bind_start'}"
        self.json_cmd_dict[u'停止绑定'] = "{'fun':'bind_stop'}"
        self.json_cmd_dict[u'设备信息'] = "{'fun':'get_device_info'}"
        self.json_cmd_dict[u'发送题目'] = "{'fun': 'answer_start','time': '2017-02-15:17:41:07:137',\
            'raise_hand': '1',\
            'attendance': '1',\
            'questions': [\
            {'type': 's','id': '1','range': 'A-D'},\
            {'type': 'm','id': '13','range': 'A-F'},\
            {'type': 'j','id': '24','range': ''},\
            {'type': 'd','id': '27','range': '1-5'},\
            {'type': 'g','id': '36','range': ''}]}"
        self.json_cmd_dict[u'查看配置'] ="{'fun':'check_config'}"
        self.json_cmd_dict[u'设置学号'] ="{'fun':'set_student_id','student_id':'1234'}"
        self.json_cmd_dict[u'设置信道'] ="{'fun': 'set_channel','tx_ch': '2','rx_ch': '6'}"
        self.json_cmd_dict[u'设置功率'] ="{'fun':'set_tx_power','tx_power':'5'}"
        self.json_cmd_dict[u'下载程序'] ="{'fun':'bootloader'}"
        self.json_cmd_dict[u'2.4g考勤'] ="{'fun':'24g_attendance','attendance_status': '1','attendance_tx_ch': '81'}"
        self.json_cmd_dict[u'DTQ 自检'] ="{'fun':'dtq_self_inspection'}"
        self.json_cmd_dict[u'开启考勤'] =u"暂无功能"
        self.json_cmd_dict[u'停止考勤'] =u"暂无功能"

        self.hex_cmd_dict   = {}
        self.hex_cmd_dict[u'清白名单'] = "5C 22 00 00 00 00 00 22 CA"
        self.hex_cmd_dict[u'开启绑定'] = "5C 41 00 00 00 00 01 01 41 CA"
        self.hex_cmd_dict[u'停止绑定'] = "5C 41 FF FF FF FF 01 00 40 CA"
        self.hex_cmd_dict[u'设备信息'] = "5C 2C 00 00 00 00 00 2C CA"
        self.hex_cmd_dict[u'发送题目'] = "5C 10 01 0C 14 55 0D 5A 00 00 00 00 00 11 03 01 01 7F 6D CA C1 CA"
        self.hex_cmd_dict[u'查看配置'] = u"暂无功能"
        self.hex_cmd_dict[u'设置学号'] = "5C 28 00 00 00 00 14 01 02 03 04 05 06 07 08 09 00 01 02 03 04 05 06 07 08 09 00 3C CA"
        self.hex_cmd_dict[u'设置信道'] = u"暂无功能"
        self.hex_cmd_dict[u'设置功率'] = u"暂无功能"
        self.hex_cmd_dict[u'下载程序'] = "5C 50 00 00 00 00 00 50 CA"
        self.hex_cmd_dict[u'2.4g考勤'] = "5C 43 00 00 00 00 02 01 51 11 CA"
        self.hex_cmd_dict[u'DTQ 自检'] = u"暂无功能"
        self.hex_cmd_dict[u'开启考勤'] = "5C 25 00 00 00 00 00 25 CA"
        self.hex_cmd_dict[u'停止考勤'] = "5C 27 00 00 00 00 00 27 CA"

        self.open_com_button=QPushButton(u"打开串口")
        self.open_com_button.setFixedSize(75, 20) 
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
        self.clear_revice_button.setFixedSize(75, 20)
        self.clear_revice_button.setStyleSheet(
            "QPushButton{border:1px solid lightgray;background:rgb(230,230,230)}"
            "QPushButton:hover{border-color:green;background:transparent}")

        self.send_cmd_combo=QComboBox(self) 
        for key in self.json_cmd_dict:
            self.send_cmd_combo.addItem(key)
        self.send_cmd_combo.setCurrentIndex(self.send_cmd_combo.
            findText(u'设备信息'))
        self.send_cmd_combo.setFixedSize(75, 40)

        self.send_lineedit = QTextEdit(u"修改或者输入指令！")
        self.send_lineedit.setFixedHeight(40)
        self.send_lineedit_button=QPushButton(u"发送")
        self.send_lineedit_button.setCheckable(False)
        self.send_lineedit_button.setAutoExclusive(False)
        self.send_lineedit_button.setFixedSize(75, 40)
        self.send_lineedit_button.setStyleSheet(
            "QPushButton{border:1px solid lightgray;background:rgb(230,230,230)}"
            "QPushButton:hover{border-color:green;background:transparent}")

        self.browser = QTextBrowser ()
        self.auto_send_chackbox = QCheckBox(u"自动发送") 
        self.auto_send_chackbox.setFixedSize(75, 20)
        self.show_time_chackbox = QCheckBox(u"显示时间")
        self.show_time_chackbox.setFixedSize(75, 20) 
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
        self.update_fm_button.setFixedSize(75, 20)
        self.update_fm_button.setStyleSheet(
            "QPushButton{border:1px solid lightgray;background:rgb(230,230,230)}"
            "QPushButton:hover{border-color:green;background:transparent}")

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
        d_hbox.addWidget(self.send_lineedit_button)
        
        self.image_button = QPushButton(u"添加固件")
        self.image_button.setCheckable(False)
        self.image_button.setAutoExclusive(False)
        self.image_button.setFixedSize(75, 20)
        self.image_button.setStyleSheet(
            "QPushButton{border:1px solid lightgray;background:rgb(230,230,230)}"
            "QPushButton:hover{border-color:green;background:transparent}")
        self.image_browser = QLineEdit()
        self.image_browser.setFixedHeight(20)
        self.image_label=QLabel(u"程序固件：")
        self.image_label.setFixedSize(75, 20)
        i_hbox = QHBoxLayout()
        i_hbox.addWidget(self.image_label)
        i_hbox.addWidget(self.image_browser)
        i_hbox.addWidget(self.image_button)

        self.script_button = QPushButton(u"添加脚本")
        self.script_button.setCheckable(False)
        self.script_button.setAutoExclusive(False)
        self.script_button.setFixedSize(75, 20)
        self.script_button.setStyleSheet(
            "QPushButton{border:1px solid lightgray;background:rgb(230,230,230)}"
            "QPushButton:hover{border-color:green;background:transparent}")
        self.script_browser = QLineEdit()
        self.script_browser.setFixedHeight(20)
        self.script_label=QLabel(u"指令脚本：")
        self.script_label.setFixedSize(75, 20)
        s_hbox = QHBoxLayout()
        s_hbox.addWidget(self.script_label)
        s_hbox.addWidget(self.script_browser)
        s_hbox.addWidget(self.script_button)

        vbox = QVBoxLayout()
        vbox.addLayout(c_hbox)
        vbox.addLayout(t_hbox)
        vbox.addLayout(i_hbox)
        vbox.addLayout(s_hbox)
        vbox.addWidget(self.browser)
        vbox.addLayout(d_hbox)
        
        self.setLayout(vbox)

        self.resize( 540, 500 )
        self.setFixedWidth( 540 )
        self.send_lineedit.setFocus()
        self.send_lineedit.setFont(QFont("Courier New", 8, False))

        self.open_com_button.clicked.connect(self.open_uart)
        self.send_lineedit_button.clicked.connect(self.uart_send_data)
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
        self.image_button.clicked.connect(self.choose_image_file)
        self.script_button.clicked.connect(self.choose_image_file)

        self.setWindowTitle(u"答题器调试工具v0.1.4")

        self.uart_listen_thread=UartListen()
        self.connect(self.uart_listen_thread,SIGNAL('protocol_message(QString)'),
            self.uart_update_text) 
        self.connect(self.uart_listen_thread,SIGNAL('download_image_info(QString)'),
            self.uart_update_download_image_info) 
        self.timer = QTimer()
        self.timer.timeout.connect(self.uart_send_data)

    def choose_image_file(self):
        global image_path

        button = self.sender()

        if button is None or not isinstance(button, QPushButton):
            return
        #print "clicked button is %s " % button.text()
        button_str = button.text()

        if button_str == u"添加固件":
            temp_image_path = unicode(QFileDialog.getOpenFileName(self, 'Open file', './'))
            if len(temp_image_path) > 0:
                self.image_browser.setText(temp_image_path)
                image_path = temp_image_path

        if button_str == u"添加脚本":
            temp_image_path = unicode(QFileDialog.getOpenFileName(self, 'Open file', './'))
            if len(temp_image_path) > 0:
                self.script_browser.setText(temp_image_path)
                self.cmd_file_name = temp_image_path

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
                self.uart_listen_thread.start()
                input_count = input_count + 1
        else:
            self.browser.append("<font color=red> Close <b>%s</b> \
                OK!</font>" % ser.portstr )
            self.open_com_button.setText(u"打开串口")
            input_count = 0
            ser.close()

    def uart_update_download_image_info(self,data):
        global ser
        global down_load_image_flag

        if down_load_image_flag == 2:
            self.uart_update_text(data)

        if data[7:8] == '2':
            ser.write('1')

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
        global image_path
        
        self.send_cmd_combo.setCurrentIndex(self.send_cmd_combo.
            findText(u'下载程序'))
        if len(image_path) > 0:
            image_size  = os.path.getsize(image_path)
            down_load_image_flag = 1
            self.process_bar = 0

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
        cursor =  self.browser.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        if data[-1] == '%':
            if self.process_bar != 0:
                cursor.movePosition(QTextCursor.End,QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.StartOfLine,QTextCursor.KeepAnchor)
                cursor.selectedText()
                cursor.removeSelectedText()
                self.browser.setTextCursor(cursor)
                self.browser.insertPlainText(data)
            else:
                self.browser.setTextCursor(cursor)
                self.browser.append(data)
            self.process_bar = self.process_bar + 1
        else:
            self.browser.setTextCursor(cursor)
            self.browser.append(data)

        logging.debug(u"接收数据：%s",data)

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
            if serial_port[:-1] == 'COM':
                try:
                    logging.info(u"尝试打开串口%s" % self.ports_dict[serial_port])
                    ser = serial.Serial( self.ports_dict[serial_port], 
                        string.atoi(baud_rate, 10))
                except serial.SerialException: 
                    logging.error(u"打开失败！")
                    pass
            else:
                logging.error(u'没有检测到设备，请接入设备！')
                self.browser.append(u"<b>Error[%d]:</b> %s" %(input_count, u'没有检测到设备，请接入设备！'))
                return
            
            if ser.isOpen() == True:
                self.browser.append("<font color=red> Open <b>%s</b> \
                    OK!</font>" % ser.portstr )
                self.open_com_button.setText(u"关闭串口")
                logging.info(u"关闭串口")
                self.uart_listen_thread.start()
                logging.info(u"启动串口监听线程!")

                data = str(self.send_lineedit.toPlainText())
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
                logging.debug(u"发送数据：%s",data)
            else:
                self.browser.append("<font color=red> Open <b>%s</b> \
                    Error!</font>" % ser.portstr )
                self.open_com_button.setText(u"关闭串口")
        else:
            if ser.isOpen() == True:
                data = str(self.send_lineedit.toPlainText())
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
                logging.debug(u"发送数据[%d]：%s" % (input_count, data))
            else:
                self.browser.append("<font color=red> Open <b>%s</b> \
                    Error!</font>" % ser.portstr )
                self.open_com_button.setText(u"关闭串口")

if __name__=='__main__':
    app = QApplication(sys.argv)
    datdebuger = DtqDebuger()
    datdebuger.show()
    app.exec_()

