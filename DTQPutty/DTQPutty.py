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

class DTQPutty(QMainWindow):
    def __init__(self, parent=None):

        super(DTQPutty, self).__init__(parent)
        self.resize(500, 500)
        self.setWindowTitle('DTQPutty V0.1.0')
        self.cmd_edit = QTextEdit()
        self.setCentralWidget(self.cmd_edit)
        self.statusBar()

        self.exit = QAction('Exit', self)
        self.exit.setShortcut('Ctrl+Q')
        self.exit.setStatusTip(u'退出')

        self.new_session = QAction('New Session', self)
        self.new_session.setShortcut('Ctrl+O')
        self.new_session.setStatusTip(u'创建一个新的会话')
        
        self.update_iamge = QAction('Update Image', self)
        self.update_iamge.setShortcut('Ctrl+U')
        self.update_iamge.setStatusTip(u'更新接收器程序 ')

        self.menubar = self.menuBar()
        self.operatopn = self.menubar.addMenu('&Operation')
        self.operatopn.addAction(self.exit)
        self.operatopn.addAction(self.new_session)
        self.image = self.menubar.addMenu('&Update Image')
        self.image.addAction(self.update_iamge)

        # 退出程序
        self.connect(self.exit, SIGNAL('triggered()'), SLOT('close()'))
        # 新的连接
        self.connect(self.new_session, SIGNAL('triggered()'), self.open_new_session)
        # 更新程序
        self.connect(self.update_iamge, SIGNAL('triggered()'), self.update_image)

    def open_new_session(self):
        com = COMSetting.get_port()
        if com :
        	self.cmd_edit.append("<font color=red> Open  <b>%s</b> OK!</font>" % com.portstr)
        else:
        	self.cmd_edit.append(u"Error:打开串口出错！")

    def update_image(self):
        com = COMSetting.get_port()
        if com :
        	self.cmd_edit.append("<font color=red> Open  <b>%s</b> OK!</font>" % com.portstr)
        else:
        	self.cmd_edit.append(u"Error:打开串口出错！")

if __name__=='__main__':
    app = QApplication(sys.argv)
    datputty = DTQPutty()
    datputty.show()
    app.exec_()

