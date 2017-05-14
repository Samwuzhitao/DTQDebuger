# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: Samwu
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
from ComSetting import *

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = 'log.txt',
    filemode = 'w',
    format = u'【%(asctime)s】 %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
)

class UartListen(QThread):
    def __init__(self,ser,parent=None):
        super(UartListen,self).__init__(parent)
        self.working  = True
        self.num      = 0
        self.ser      = ser
        self.input_count      = 0
        self.show_time_flag   = 0
        self.decode_type_flag = 0
        self.hex_decode_show_style = 1
        self.down_load_image_flag  = 0
        self.image_path            = ''
        self.info_str = ''
        self.hex_revice    = HexDecode()
        self.json_revice   = JsonDecode()
        self.bin_decode    = BinDecode()
        self.ReviceFunSets = {
            0:self.uart_down_load_image_0,
            1:self.uart_down_load_image_1,
            2:self.uart_down_load_image_2,
            3:self.uart_down_load_image_3,
        }
        self.DecodeFunSets = {
            0:self.json_revice.r_machine,
            1:self.hex_revice.r_machine,
        }

    def __del__(self):
        self.working=False
        self.wait()

    def uart_down_load_image_0(self,read_char):
        recv_str      = ""
        ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'
        self.hex_revice.show_style = self.hex_decode_show_style
        str1 = self.DecodeFunSets[self.decode_type_flag](read_char)

        if str1 :
            now = time.strftime( ISOTIMEFORMAT,
                time.localtime(time.time()))
            if self.show_time_flag == 1:
                recv_str = u"[%s] DTQ@%s:~$ R[%d]: " %
                           (now, self.ser.portstr, self.input_count) + u"%s" %  str1
            else:
                recv_str = u"DTQ@%s:~$ R[%d]: " %
                           (self.ser.portstr, self.input_count) + u"%s" % str1
            #print recv_str
        return 0,recv_str

    def uart_down_load_image_1(self,read_char):
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
        recv_str = ""
        retuen_flag = 2

        if read_char == 'C':
            recv_str = u"STEP[2]:发送镜像信息..."

            ack = '06'
            ack = ack.decode("hex")
            ser.write(ack)
            #print image_path
            data = self.bin_decode.soh_pac(self.image_path)

            if self.bin_decode.file_size > 0:
                retuen_flag = 3
                self.ser.write(data)
            else:
                recv_str = u"ERROR:文件内容为空！"
                self.ser.write('a')
                retuen_flag = 0

        return retuen_flag,recv_str

    def uart_down_load_image_3(self,read_char):
        recv_str = ""
        retuen_flag = 3

        char = "%02X" % ord(read_char)
        if self.bin_decode.over == 3:
            self.info_str += read_char
            #print self.info_str
            if char == '0A':
                recv_str = self.info_str
                self.info_str = ''
                if recv_str[0:5] == 'Start':
                    retuen_flag = 0
                    self.bin_decode.clear()

        #print "%s self.bin_decode.over = %d" % (char,self.bin_decode.over)
        if char == '06':
            # print " File index = %d sum = %d" % (self.bin_decode.send_index, self.bin_decode.file_size)
            revice_rate = self.bin_decode.send_index*100.0 / self.bin_decode.file_size
            temp_str = int(revice_rate / 2.5)*'#' + (40-int(revice_rate / 2.5))*' '

            recv_str = u"STEP[3]:传输镜像文件：%s %3d%%" % (temp_str,revice_rate)

            if self.bin_decode.over == 0:
                self.ser.write(self.bin_decode.stx_pac())

            if self.bin_decode.over == 1:
                eot = '04'
                #print eot
                eot = eot.decode("hex")
                self.ser.write(eot)
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
        while self.working==True:
            if self.ser.isOpen() == True:
                read_char = self.ser.read(1)

                #print "status = %d char = %02X " % (down_load_image_flag, ord(read_char))
                next_flag,recv_str = self.ReviceFunSets[self.down_load_image_flag]( read_char )

                if recv_str :
                    if self.down_load_image_flag != 1:
                        self.emit(SIGNAL('protocol_message(QString)'),recv_str)
                        #print 'protocol_message(QString)',
                    else:
                        self.emit(SIGNAL('download_image_info(QString)'),recv_str )
                    #print "status = %d char = %s str = %s" % (self.down_load_image_flag, read_char, recv_str)
                self.down_load_image_flag = next_flag

class DTQPutty(QMainWindow):
    def __init__(self, parent=None):
        self.process_bar = 0
        self.com_monitor_dict = {}
        super(DTQPutty, self).__init__(parent)
        self.resize(600, 500)
        self.setWindowTitle('DTQPutty V0.1.0')
        self.setFont(QFont("Courier New", 8, False))
        self.cmd_edit = QTextEdit()
        self.cmd_edit.setStyleSheet('QWidget {background-color:#111111}')
        self.cmd_edit.setTextColor(QColor(200,200,200))
        self.setCentralWidget(self.cmd_edit)

        self.dock1=QDockWidget(u"当前连接",self)
        self.dock1.setFeatures(QDockWidget.DockWidgetMovable)
        self.dock1.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.te1=QListWidget()
        self.te1.setFixedWidth(100)
        self.dock1.setWidget(self.te1)
        self.addDockWidget(Qt.LeftDockWidgetArea,self.dock1)

        self.statusBar()
        self.menubar = self.menuBar()

        self.exit = QAction('Exit', self)
        self.exit.setShortcut('Ctrl+Q')
        self.exit.setStatusTip(u'退出')

        self.new_session = QAction('New Session', self)
        self.new_session.setShortcut('Ctrl+O')
        self.new_session.setStatusTip(u'创建一个新的会话')

        self.operatopn = self.menubar.addMenu(u'&设置')
        self.operatopn.addAction(self.exit)
        self.operatopn.addAction(self.new_session)

        self.update_iamge = QAction(u'更新镜像', self)
        self.update_iamge.setShortcut('Ctrl+U')
        self.update_iamge.setStatusTip(u'更新接收器程序')

        self.image = self.menubar.addMenu(u'&工具')
        self.image.addAction(self.update_iamge)

        self.dis_connect = QAction(u'断开连接', self)
        self.dis_connect.setShortcut('Ctrl+D')
        self.dis_connect.setStatusTip(u'断开与接收器的连接')

        self.re_connect = QAction(u'重新连接', self)
        self.re_connect.setShortcut('Ctrl+R')
        self.re_connect.setStatusTip(u'重新连接接收器')

        self.connection = self.menubar.addMenu(u'&连接管理')
        self.connection.addAction(self.dis_connect)
        self.connection.addAction(self.re_connect)

        # 退出程序
        self.connect(self.exit, SIGNAL('triggered()'), SLOT('close()'))
        # 新的连接
        self.connect(self.new_session, SIGNAL('triggered()'), self.open_new_session)
        # 更新程序
        self.connect(self.update_iamge, SIGNAL('triggered()'), self.update_image)


    def open_new_session(self):
        com = COMSetting.get_port()
        if com :
            self.cmd_edit.append("Open %s OK!" % com.portstr)
            logging.info(u"打开串口")
            self.te1.addItem(com.portstr)
            self.com_monitor_dict[com.portstr] = UartListen(com)
            self.connect(self.com_monitor_dict[com.portstr],
                         SIGNAL('protocol_message(QString)'),
                         self.uart_update_text)
            self.connect(self.com_monitor_dict[com.portstr],
                         SIGNAL('download_image_info(QString)'),
                         self.uart_update_download_image_info)
            self.com_monitor_dict[com.portstr].start()
            self.setWindowTitle(com.portstr + '-DTQPutty V0.1.0')
            logging.info(u"启动串口监听线程!")
        else:
            self.cmd_edit.append(u"Error:打开串口出错！")

    def update_image(self):
        com = COMSetting.get_port()
        if com :
            self.cmd_edit.append("Open %s OK!" % com.portstr)
        else:
            self.cmd_edit.append(u"Error:打开串口出错！")

    def uart_update_download_image_info(self,data):
        global ser
        global down_load_image_flag

        if down_load_image_flag == 2:
            self.uart_update_text(data)

        if data[7:8] == '2':
            ser.write('1')

    def uart_update_text(self,data):
        cursor =  self.cmd_edit.textCursor()
        cursor.movePosition(QTextCursor.End)

        if data[-1] == '%':
            if self.process_bar != 0:
                cursor.movePosition(QTextCursor.End,QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.StartOfLine,QTextCursor.KeepAnchor)
                cursor.selectedText()
                cursor.removeSelectedText()
                self.cmd_edit.setTextCursor(cursor)
                self.cmd_edit.insertPlainText(data)
            else:
                self.cmd_edit.setTextCursor(cursor)
                self.cmd_edit.append(data)
            self.process_bar = self.process_bar + 1
        else:
            self.cmd_edit.setTextCursor(cursor)
            self.cmd_edit.append(data)
        #print data
        logging.debug(u"接收数据：%s",data)

if __name__=='__main__':
    app = QApplication(sys.argv)
    datputty = DTQPutty()
    datputty.show()
    app.exec_()

