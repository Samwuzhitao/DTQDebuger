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
from ComMonitor import *

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = 'log.txt',
    filemode = 'w',
    format = u'【%(asctime)s】 %(filename)s [line:%(lineno)d] %(message)s',
)

ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'

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
        self.add_script_fun1(u'./data/功能测试指令.inf',1)

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
        # print item
        script_name = unicode(item.text(0))
        # print script_name
        # print self.json_cmd_dict
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
            self.com_monitor_dict[com.portstr] = ComMonitor(com)
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

    def add_script_fun1(self,file_path,mode):
        # print file_path
        f = open(file_path,'rU')
        lines = f.readlines()
        f.close()

        for line_no in range(len(lines)):
            # print (line_no,lines[line_no][0:5])
            if lines[line_no][0:5] == u"[cmd]":
                start_line = line_no
                # print start_line
            if lines[line_no][0:5] == u"[enco":
                encode_style = lines[line_no+1]

        name = unicode(file_path.split("/")[-1])
        new_script = QTreeWidgetItem(self.tree_script)
        new_script.setText(0, name.split(".")[0] + "(%s)" % encode_style[0:3])

        cmds = lines[start_line+1:]

        for i in range(len(cmds)/2):
            item = cmds[i*2].strip('\n')
            item = unicode(item.decode('utf-8'))

            if item[0:1] == u"<":
                cmd_dsc = item[4:]
            else:
               cmd_dsc = item[0:]
            #print cmd_dsc
            cmd = cmd_dsc.split(":")[0]

            if mode == 1:
                self.json_cmd_key.append(cmd )
                # print "cmd = %s" % cmd
                self.json_cmd_dict[cmd] = cmds[i*2+1].strip('\n')
                # print "value = %s" % self.json_cmd_dict[cmd]
                # print " index = %02d cmds = %s str_cmd = %s" % (i,cmd,self.json_cmd_dict[cmd])
            QTreeWidgetItem(new_script).setText(0, cmd)

    def add_script_fun(self):
        temp_image_path = unicode(QFileDialog.getOpenFileName(self, 'Open file', './', "txt files(*.inf)"))
        self.add_script_fun1(temp_image_path,0)

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

