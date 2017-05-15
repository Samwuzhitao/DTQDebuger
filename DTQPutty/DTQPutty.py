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
    format = u'【%(asctime)s】 %(filename)s [line:%(lineno)d] %(message)s',
)

ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'

class UartListen(QThread):
    def __init__(self,com,parent=None):
        super(UartListen,self).__init__(parent)
        self.working  = True
        self.num      = 0
        self.com      = com
        print self.com
        self.input_count      = 0
        self.decode_type_flag = 0
        self.hex_decode_show_style = 1
        self.down_load_image_flag  = 0
        self.image_path            = ''
        self.info_str = ''
        self.hex_revice    = HexDecode()
        self.json_revice   = JsonDecode()
        self.bin_decode    = BinDecode()
        self.ReviceFunSets = {
            0:self.uart_cmd_decode,
            1:self.uart_print_decode,
            2:self.uart_image_start,
            3:self.uart_image_transport,
        }
        self.DecodeFunSets = {
            0:self.json_revice.r_machine,
            1:self.hex_revice.r_machine,
        }

    def __del__(self):
        self.working=False
        self.wait()

    def uart_cmd_decode(self,read_char):
        recv_str      = ""

        self.hex_revice.show_style = self.hex_decode_show_style
        str1 = self.DecodeFunSets[self.decode_type_flag](read_char)

        if str1 :
            recv_str =  str1

        return 0,recv_str

    def uart_print_decode(self,read_char):
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

    def uart_image_start(self,read_char):
        recv_str = ""
        retuen_flag = 2

        if read_char == 'C':
            recv_str = u"STEP[2]:发送镜像信息..."

            ack = '06'
            ack = ack.decode("hex")
            com.write(ack)
            #print image_path
            data = self.bin_decode.soh_pac(self.image_path)

            if self.bin_decode.file_size > 0:
                retuen_flag = 3
                self.com.write(data)
            else:
                recv_str = u"ERROR:文件内容为空！"
                self.com.write('a')
                retuen_flag = 0

        return retuen_flag,recv_str

    def uart_image_transport(self,read_char):
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
                self.com.write(self.bin_decode.stx_pac())

            if self.bin_decode.over == 1:
                eot = '04'
                #print eot
                eot = eot.decode("hex")
                self.com.write(eot)
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
            if self.com.isOpen() == True:
                read_char = self.com.read(1)

                #print "status = %d char = %02X " % (down_load_image_flag, ord(read_char))
                next_flag,recv_str = self.ReviceFunSets[self.down_load_image_flag]( read_char )

                if recv_str :
                    if self.down_load_image_flag != 1:
                        self.emit(SIGNAL('protocol_message(QString, QString)'),self.com.portstr,recv_str)
                        #print 'protocol_message(QString)',
                    else:
                        self.emit(SIGNAL('download_image_info(QString, QString)'),self.com.portstr,recv_str )
                    #print "status = %d char = %s str = %s" % (self.down_load_image_flag, read_char, recv_str)
                self.down_load_image_flag = next_flag

class DTQPutty(QMainWindow):
    def __init__(self, parent=None):
        super(DTQPutty, self).__init__(parent)
        self.process_bar = 0
        self.com_monitor_dict = {}
        self.com_dict         = {}
        self.com_edit_dict    = {}
        self.com_window_dict  = {}
        self.mearge_flag      = 0
        self.json_cmd_dict    = {}
        self.json_cmd_key     = []

        self.json_cmd_key.append(u'01.清白名单')
        self.json_cmd_dict[self.json_cmd_key[0]] = "{'fun':'clear_wl'}"
        self.json_cmd_key.append(u'02.开启绑定')
        self.json_cmd_dict[self.json_cmd_key[1]] = "{'fun':'bind_start'}"
        self.json_cmd_key.append(u'03.停止绑定')
        self.json_cmd_dict[self.json_cmd_key[2]] = "{'fun':'bind_stop'}"
        self.json_cmd_key.append(u'04.设备信息')
        self.json_cmd_dict[self.json_cmd_key[3]] = "{'fun':'get_device_info'}"
        self.json_cmd_key.append(u'05.发送题目')
        self.json_cmd_dict[self.json_cmd_key[4]] = "{'fun': 'answer_start','time': '2017-02-15:17:41:07:137',\
            'raise_hand': '1',\
            'attendance': '1',\
            'questions': [\
            {'type': 's','id': '1','range': 'A-D'},\
            {'type': 'm','id': '13','range': 'A-F'},\
            {'type': 'j','id': '24','range': ''},\
            {'type': 'd','id': '27','range': '1-5'},\
            {'type': 'g','id': '36','range': ''}]}"
        self.json_cmd_key.append(u'06.查看配置')
        self.json_cmd_dict[self.json_cmd_key[5]] = "{'fun':'check_config'}"
        self.json_cmd_key.append(u'07.设置学号')
        self.json_cmd_dict[self.json_cmd_key[6]] = "{'fun':'set_student_id','student_id':'1234'}"
        self.json_cmd_key.append(u'08.设置信道')
        self.json_cmd_dict[self.json_cmd_key[7]] = "{'fun': 'set_channel','tx_ch': '2','rx_ch': '6'}"
        self.json_cmd_key.append(u'09.设置功率')
        self.json_cmd_dict[self.json_cmd_key[8]] = "{'fun':'set_tx_power','tx_power':'5'}"
        self.json_cmd_key.append(u'10.下载程序')
        self.json_cmd_dict[self.json_cmd_key[9]] = "{'fun':'bootloader'}"
        self.json_cmd_key.append(u'11.2.4g考勤')
        self.json_cmd_dict[self.json_cmd_key[10]] = "{'fun':'24g_attendance','attendance_status': '1',\
            'attendance_tx_ch': '81'}"
        self.json_cmd_key.append(u'12.DTQ 自检')
        self.json_cmd_dict[self.json_cmd_key[11]] = "{'fun':'dtq_self_inspection'}"
        self.json_cmd_key.append(u'13.开启考勤')
        self.json_cmd_dict[self.json_cmd_key[12]] = u"暂无功能"
        self.json_cmd_key.append(u'14.停止考勤')
        self.json_cmd_dict[self.json_cmd_key[13]] = u"暂无功能"

        self.resize(700, 600)
        self.setWindowTitle('DTQPutty V0.1.0')
        self.workSpace = QWorkspace()
        self.setCentralWidget(self.workSpace)

        self.create_new_window("CONSOLE")
        self.com_window_dict["CONSOLE"].show()
        self.com_window_dict["CONSOLE"].showMaximized()

        self.dock_com = QDockWidget(u"当前连接",self)
        self.dock_com.setFeatures(QDockWidget.DockWidgetMovable)
        self.dock_com.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.tree_com = QTreeWidget()
        self.tree_com.setFont(QFont("Courier New", 8, False))
        self.tree_com.setColumnCount(2)
        self.tree_com.setHeaderLabels([u'连接名',u'参数'])
        self.tree_com.setColumnWidth(0, 90)
        self.tree_com.setColumnWidth(1, 50)
        self.tree_com.setFixedWidth(150)
        self.tree_com.setFixedHeight(200)
        self.root_com = QTreeWidgetItem(self.tree_com)
        self.root_com.setText(0, "CONSOLE")
        self.root_com.setText(1, "NONE")
        self.dock_com.setWidget(self.tree_com)
        self.addDockWidget(Qt.LeftDockWidgetArea,self.dock_com)

        self.dock_script = QDockWidget(u"指令 & 脚本",self)
        self.dock_script.setFeatures(QDockWidget.DockWidgetMovable)
        self.dock_script.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        self.tree_script = QTreeWidget()
        self.tree_script.setFont(QFont("Courier New", 8, False))
        self.tree_script.setColumnCount(1)
        self.tree_script.setHeaderLabel(u'测试脚本')
        self.tree_script.setColumnWidth(0, 90)
        self.tree_script.setFixedWidth(150)
        self.function_script = QTreeWidgetItem(self.tree_script)
        self.function_script.setText(0, u"功能测试指令")
        for item in self.json_cmd_key:
            QTreeWidgetItem(self.function_script).setText(0,item)

        self.power_script = QTreeWidgetItem(self.tree_script)
        self.power_script.setText(0, u"功耗测试脚本")
        child1 = QTreeWidgetItem(self.power_script)
        child1.setText(0,u'设备信息')

        self.dock_script.setWidget(self.tree_script)
        self.addDockWidget(Qt.LeftDockWidgetArea,self.dock_script)

        self.statusBar()
        self.menubar = self.menuBar()
        # 设置
        self.exit = QAction('Exit', self)
        self.exit.setShortcut('Ctrl+Q')
        self.exit.setStatusTip(u'退出')
        self.dis_connect = QAction(u'断开连接', self)
        self.dis_connect.setShortcut('Ctrl+D')
        self.dis_connect.setStatusTip(u'断开与接收器的连接')
        self.new_session = QAction('New Session', self)
        self.new_session.setShortcut('Ctrl+O')
        self.new_session.setStatusTip(u'创建一个新的会话')
        self.re_connect = QAction(u'重新连接', self)
        self.re_connect.setShortcut('Ctrl+R')
        self.re_connect.setStatusTip(u'重新连接接收器')
        self.connection = self.menubar.addMenu(u'&设置')
        self.connection.addAction(self.new_session)
        self.connection.addAction(self.dis_connect)
        self.connection.addAction(self.re_connect)
        self.connection.addAction(self.exit)
        # 工具
        self.update_iamge = QAction(u'更新镜像', self)
        self.update_iamge.setShortcut('Ctrl+U')
        self.update_iamge.setStatusTip(u'更新接收器程序')
        self.add_script = QAction(u'添加脚本', self)
        self.add_script.setShortcut('Ctrl+A')
        self.add_script.setStatusTip(u'添加指令脚本')
        self.tool = self.menubar.addMenu(u'&工具')
        self.tool.addAction(self.update_iamge)
        self.tool.addAction(self.add_script)
        # 窗口
        self.tile = QAction(u"平铺",self)
        self.tile.setShortcut('Ctrl+T')
        self.merge = QAction(u"合并",self)
        self.merge.setShortcut('Ctrl+M')
        self.window = self.menubar.addMenu(u'&窗口')
        self.window.addAction(self.tile)
        self.window.addAction(self.merge)
        self.connect(self.tile,SIGNAL("triggered()"),self.workSpace,SLOT("tile()"))
        self.connect(self.merge,SIGNAL("triggered()"),self.merge_display)

        # 退出程序
        self.connect(self.exit, SIGNAL('triggered()'), SLOT('close()'))
        # 新的连接
        self.connect(self.new_session, SIGNAL('triggered()'), self.open_new_session)
        # 更新程序
        self.connect(self.add_script, SIGNAL('triggered()'), self.add_script_fun)
        # 串口连接管理
        self.connect(self.tree_com, SIGNAL("itemDoubleClicked (QTreeWidgetItem *,int)"),
            self.tree_com_itemDoubleClicked)
        # 脚本指令操作
        self.connect(self.tree_script, SIGNAL("itemDoubleClicked (QTreeWidgetItem *,int)"),
            self.tree_script_itemDoubleClicked)

    def tree_com_itemDoubleClicked(self,item, column):
        com_name = unicode(item.text(0))
        if com_name[0:2] == 'CO':
            self.com_window_dict[com_name].show()

    def tree_script_itemDoubleClicked(self,item, column):
        script_name = unicode(item.text(0))

        for item in self.com_dict:
            self.com_monitor_dict[item].input_count = self.com_monitor_dict[item].input_count + 1
            index  = u"<font color=lightgreen>S[%d]:</font>" % self.com_monitor_dict[item].input_count
            self.uart_update_text(item,index, self.json_cmd_dict[script_name])
            self.com_dict[item].write(self.json_cmd_dict[script_name])

    def create_new_window(self,name):
        # 创建显示窗口
        self.com_window_dict[name] = QMainWindow()
        self.com_window_dict[name].setWindowTitle(name)
        self.com_edit_dict[name] = QTextEdit()
        self.com_edit_dict[name].setStyleSheet('QWidget {background-color:#111111}')
        self.com_edit_dict[name].setFont(QFont("Courier New", 10, False))
        self.com_edit_dict[name].setTextColor(QColor(200,200,200))
        self.com_window_dict[name].setCentralWidget(self.com_edit_dict[name])
        self.com_edit_dict[name].append("Open %s OK!" % name)
        self.workSpace.addWindow(self.com_window_dict[name])

    def open_new_session(self):
        com = COMSetting.get_port()
        if com :
            # 增加配置信息显示
            logging.info(u"打开串口")
            self.root_com = QTreeWidgetItem(self.tree_com)
            self.root_com.setText(0, com.portstr)
            child1 = QTreeWidgetItem(self.root_com)
            child1.setText(0,'SPEED')
            child1.setText(1, "%d" % com.baudrate)

            # 创建显示窗口
            self.create_new_window(com.portstr)

            # 创建监听线程
            self.com_monitor_dict[com.portstr] = UartListen(com)
            self.com_dict[com.portstr]         = com

            self.connect(self.com_monitor_dict[com.portstr],
                         SIGNAL('protocol_message(QString, QString)'),
                         self.update_edit)
            self.connect(self.com_monitor_dict[com.portstr],
                         SIGNAL('download_image_info(QString, QString)'),
                         self.uart_update_download_image_info)

            self.com_monitor_dict[com.portstr].start()
            self.setWindowTitle(com.portstr + '-DTQPutty V0.1.0')
            logging.info(u"启动串口监听线程!")
        else:
            self.com_edit_dict["CONSOLE"].append(u"Error:打开串口出错！")

    def add_script_fun(self):
        temp_image_path = unicode(QFileDialog.getOpenFileName(self, 'Open file', './', "txt files(*.inf)"))

        f = open(temp_image_path,'rU')
        cmds =f.readlines()
        #print cmds
        f.close()
        name = unicode(temp_image_path.split("/")[-1])
        new_script = QTreeWidgetItem(self.tree_script)
        new_script.setText(0, name.split(".")[0] )

        for i in range(len(cmds)/2):
            item = cmds[i*2]
            item = unicode(item.decode('utf-8'))
            if item[0:1] == "<":
                cmd_dsc = item[4:]
            else:
               cmd_dsc = item[0:]
            #print cmd_dsc
            QTreeWidgetItem(new_script).setText(0, cmd_dsc.split(":")[0])

    def uart_update_download_image_info(self,ser_str,data):
        global down_load_image_flag

        if down_load_image_flag == 2:
            self.uart_update_text(ser_str,data)

        if data[7:8] == '2':
            self.com_monitor_dict[com.portstr].com.write('1')

    def merge_display(self):
        if self.mearge_flag == 0:
            self.mearge_flag = 1
        else:
            self.mearge_flag = 0

    def update_edit(self,ser_str,data):
        index  = u"<font color=lightgreen>R[%d]:</font>" % self.com_monitor_dict[str(ser_str)].input_count
        self.uart_update_text(str(ser_str), index, data)

    def uart_update_text(self,ser_str,index,data):
        logging.debug(u"接收数据：%s",data)

        if self.mearge_flag == 0:
            ser = "CONSOLE"
        else:
            ser = str(ser_str)

        cursor = self.com_edit_dict[ser].textCursor()
        cursor.movePosition(QTextCursor.End)

        now = time.strftime( ISOTIMEFORMAT,time.localtime(time.time()))
        header = u"<font color=green>[%s]@%s:~$ </font>" % (now, ser_str)

        data = header + index + u"<font color=white>%s</font>" %  data

        if data[-1] == '%':
            if self.process_bar != 0:
                cursor.movePosition(QTextCursor.End,QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.StartOfLine,QTextCursor.KeepAnchor)
                cursor.selectedText()
                cursor.removeSelectedText()
                self.com_edit_dict[ser].setTextCursor(cursor)
                self.com_edit_dict[ser].insertPlainText(data)
            else:
                self.com_edit_dict[ser].setTextCursor(cursor)
                self.com_edit_dict[ser].append(data)
            self.process_bar = self.process_bar + 1
        else:
            self.com_edit_dict[ser].setTextCursor(cursor)
            self.com_edit_dict[ser].append(data)
        #print data

if __name__=='__main__':
    app = QApplication(sys.argv)
    datputty = DTQPutty()
    datputty.show()
    app.exec_()

