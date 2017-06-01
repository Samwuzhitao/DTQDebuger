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
import json
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from JsonDecode   import *

ser           = 0
input_count   = 0
LOGTIMEFORMAT = '%Y%m%d'
log_time      = time.strftime( LOGTIMEFORMAT,time.localtime(time.time()))
log_name      = "log-%s.txt" % log_time 

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = log_name,
    filemode = 'w',
    format = u'【%(asctime)s】 %(levelname)s %(message)s',
)

class UartListen(QThread):
    def __init__(self,parent=None):
        super(UartListen,self).__init__(parent)
        self.working       = True
        self.num           = 0
        self.json_revice   = JsonDecode()
        self.ReviceFunSets = { 0:self.uart_down_load_image_0 }

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
            recv_str = u"R[%d]: %s" % (input_count-1,str1)
        return recv_str

    def run(self):
        global ser

        while self.working==True:
            if ser.isOpen() == True:
                read_char = ser.read(1)
                recv_str  = self.ReviceFunSets[0]( read_char )
                if len(recv_str) > 0:
                    self.emit(SIGNAL('output(QString)'),recv_str)

class QtqBurner(QWidget):
    def __init__(self, parent=None):
        global ser

        super(QtqBurner, self).__init__(parent)
        input_count = 0
        self.ports_dict = {}
        self.dtq_image_path = ''
        self.new_image_path = ''
        self.dtq_id         = ''
        self.pro_dict = {
        u'我司':0,
        u'江西移动':1,
        u'重庆移动':2,
        u'内蒙移动':3,
        u'广西移动(初稿)':4,
        u'广西移动(定稿)':5,
        u'贵州移动':6,
        u'甘肃移动':7,
        u'山西移动_天波':8,
        u'山西移动_鑫诺':9,
        u'山西移动_统一协议':10,
        u'安徽移动':11,
        u'四川移动':12
        }
        self.setWindowTitle(u"烧录工具v0.1.1")

        self.com_combo=QComboBox(self)
        self.com_combo.setFixedSize(75, 20)
        self.uart_scan(self.ports_dict)
        self.start_button = QPushButton(u"打开接收器")
        self.clear_button = QPushButton(u"清空LOG信息")
        c_hbox = QHBoxLayout()
        c_hbox.addWidget(self.com_combo)
        c_hbox.addWidget(self.start_button)
        
        c_hbox.addWidget(self.clear_button)

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

        self.dtq_tabwidget = QTabWidget()
        self.dtq_tabwidget.setFixedHeight(65)
       
        self.dtq_wiget    = QWidget()
        self.boot_button  = QPushButton(u"答题器固件")
        self.boot_browser = QLineEdit()
        self.boot_label=QLabel(u"文件:")
        self.save_button  = QPushButton(u"手动转换文件")
        dtq_layout = QHBoxLayout()
        dtq_layout.addWidget(self.boot_label)
        dtq_layout.addWidget(self.boot_browser)
        dtq_layout.addWidget(self.boot_button)
        dtq_layout.addWidget(self.save_button)

        self.yyk_wiget = QWidget()
        self.pro_combo = QComboBox(self)
        self.pro_combo.addItems([
            u'我司',
            u'江西移动',
            u'重庆移动',
            u'内蒙移动',
            u'广西移动(初稿)',
            u'广西移动(定稿)',
            u'贵州移动',
            u'甘肃移动',
            u'山西移动_天波',
            u'山西移动_鑫诺',
            u'山西移动_统一协议',
            u'安徽移动',
            u'四川移动'])
        self.pro_label = QLabel(u"选择协议:")
        self.pro_label.setFixedSize(60, 20)
        self.pro_button = QPushButton(u"生效协议")
        yyk_layout = QHBoxLayout()
        yyk_layout.addWidget(self.pro_label)
        yyk_layout.addWidget(self.pro_combo)
        yyk_layout.addWidget(self.pro_button)

        self.dtq_wiget.setLayout(dtq_layout)
        self.yyk_wiget.setLayout(yyk_layout)

        self.dtq_tabwidget.addTab(self.dtq_wiget, "&DTQ")
        self.dtq_tabwidget.addTab(self.yyk_wiget, "&YYK")

        self.browser = QTextBrowser()
        self.browser.setFont(QFont("Courier New", 10, QFont.Bold))
        self.burn_button = QPushButton(u"手动烧录(DTQ)")
        self.burn_button.setFont(QFont("Courier New", 14, QFont.Bold))
        self.burn_button.setFixedHeight(40)
        vbox = QVBoxLayout()

        vbox.addWidget(self.dtq_tabwidget)
        vbox.addWidget(self.browser)
        vbox.addWidget(self.burn_button)

        box = QVBoxLayout()
        box.addLayout(c_hbox)
        box.addLayout(e_hbox)

        box.addLayout(vbox)
        self.setLayout(box)
        self.resize( 580, 500 )

        self.boot_button.clicked.connect(self.choose_image_file)
        self.burn_button.clicked.connect(self.download_image)
        self.clear_button.clicked.connect(self.clear_text)
        self.pro_button.clicked.connect(self.yyk_update_pro)

        self.start_button.clicked.connect(self.band_start)
        self.save_button.clicked.connect(self.exchange_file)
        self.uart_listen_thread=UartListen()
        self.connect(self.uart_listen_thread,SIGNAL('output(QString)'),
            self.uart_update_text)
        self.com_combo.currentIndexChanged.connect(self.change_uart)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def yyk_update_pro(self):
        global input_count
        global ser

        pro_name = unicode(self.pro_combo.currentText())

        if ser.isOpen() == True:
            cmd = '{"fun": "si24r2e_auto_burn","setting": "1","pro_index": "%d"}'  %  self.pro_dict[pro_name]
            ser.write(cmd)
            input_count = input_count + 1
            data = u"S[%d]: " % (input_count-1) + u"%s" % cmd
            self.uart_update_text(data)

    def update_time(self):
        self.time_lineedit.setText(time.strftime(
            '%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

    def clear_text(self):
        self.browser.clear()

    def change_uart(self):
        global input_count
        global ser
        self.uart_scan(self.ports_dict)
        if ser != 0:
            input_count = 0
            ser.close()

    def uart_update_text(self,data):
        json_dict = {}
        if data[0] == 'R':
            json_str = data[6:]
            # print json_str
            json_dict = json.loads(str(json_str))
            print json_dict
        if json_dict.has_key(u"fun") == True:
            fun = json_dict[u"fun"]
            if fun == u"update_card_info":
                self.dtq_id = json_dict[u"card_id"]
                self.dtq_id_lineedit.setText(self.dtq_id)
                self.exchange_file()

        if json_dict.has_key(u"fun") == True:
            fun = json_dict[u"fun"]
            if fun == u"card_setting":
                if json_dict.has_key(u"result") == True:
                    result = json_dict[u"result"]
                    pro_name = json_dict[u"pro_name"]
                    self.dtq_id = json_dict[u"card_id"]
                    self.dtq_id_lineedit.setText(self.dtq_id)
                    if result == u"0":
                        self.browser.append(u"<font color=green>%s@UID:[%s] 卡片配置成功！" % (pro_name,self.dtq_id))
                        logging.debug(u"%s@UID:[%s] 卡片配置成功！" % (pro_name,self.dtq_id))
                    if result == u"-1":
                        self.browser.append(u"<font color=red>%s@UID:[%s] 卡片配置失败:烧写失败！" % (pro_name,self.dtq_id))
                        logging.debug(u"%s@UID:[%s] 卡片配置失败:烧写失败！" % (pro_name,self.dtq_id))
                    if result == u"-2":
                        self.browser.append(u"<font color=red>%s@UID:[%s] 卡片配置失败:烧写次数达到上限！" % (pro_name,self.dtq_id))
                        logging.debug(u"%s@UID:[%s] 卡片配置失败:烧写次数达到上限！" % (pro_name,self.dtq_id))

            if fun == u"rssi_check":
                if json_dict.has_key(u"result") == True:
                    result = json_dict[u"result"]
                    rssi   = json_dict[u"check_rssi"]
                    pro_name = json_dict[u"pro_name"]
                    if result == u"0":
                        self.browser.append(u"<font color=green>%s@UID:[%s] RSSI校验成功！RSSI = %s" % (pro_name,self.dtq_id,rssi))
                        logging.debug(u"%s@UID:[%s] RSSI校验成功！RSSI = %s" % (pro_name,self.dtq_id,rssi))
                    else:
                        self.browser.append(u"<font color=red>%s@UID:[%s] RSSI校验失败！" % (pro_name,self.dtq_id))
                        logging.debug(u"%s@UID:[%s] RSSI校验失败！" % (pro_name,self.dtq_id))

            if fun == u"si24r2e_auto_burn":
                if json_dict.has_key(u"result") == True:
                    result = json_dict[u"result"]
                    pro_name = json_dict[u"pro_name"]
                    if result == u"0":
                        self.browser.append(u"<font color=green>设置协议:[%s] 成功!" % pro_name )
                        logging.debug(u"设置协议:[%s] 成功!" % pro_name )
                    else:
                        self.browser.append(u"<font color=red>%s@设置协议:[%s] 失败!" % pro_name )
                        logging.debug(u"设置协议:[%s] 失败!" % pro_name )
                    
            if fun == u"bind_start":
                if json_dict.has_key(u"result") == True:
                    result = json_dict[u"result"]
                    if result == u"0":
                        self.browser.append(u"<font color=green>开启成功!" )
                        logging.debug(u"开启成功!" )
                    else:
                        self.browser.append(u"<font color=red>开启失败!" )
                        logging.debug(u"开启失败!" )
        else:
            self.browser.append(data)

    def uart_scan(self,dict):
        for i in range(256):

            try:
                s = serial.Serial(i)
                if dict.has_key(s.portstr) == False:
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
        if self.dtq_image_path :
            f = open(self.dtq_image_path)
            li = f.readlines()
            f.close()

            time_data = time.strftime( '%Y%m%d',time.localtime(time.time()))
            insert_data = "04FC0000" + time_data
            insert_data_hex = insert_data.decode("hex")

            check_sum = 0
            for i in insert_data_hex:
                check_sum = (ord(i) + check_sum) % 0x100

            insert_data = ':' + insert_data + "%02X\n" % (0x100-check_sum)
            li.insert(1, insert_data)
            #print li
            file_path = self.dtq_image_path[0:len(self.dtq_image_path)-4]
            self.new_image_path = file_path + "_NEW.hex"
            new_file = open(self.new_image_path ,'w')
            for i in li:
                new_file.write(i)
            new_file.close()

            self.browser.append(u"<font color=green>DTQ@UID:[%s] HEX文件转换成功！" %
                str(self.dtq_id_lineedit.text()) )
        else:
            self.browser.append(u"<font color=red>DTQ@错误：无原始文件！")

    def band_start(self):
        global ser
        global input_count

        self.open_uart()
        if ser.isOpen() == True:
            self.uart_listen_thread.start()
            cmd = "{'fun':'bind_start'}"
            ser.write(cmd)
            input_count = input_count + 1
            data = u"S[%d]: " % (input_count-1) + u"%s" % cmd
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
            if self.dtq_image_path > 0:
                self.boot_browser.setText(self.dtq_image_path)

    def download_image(self):
        path = os.path.abspath("./")
        exe_file_path = path + '\\system\\' + 'nrfjprog.exe'
        cmd1 = exe_file_path + ' -e --program ' + self.new_image_path
        # print cmd1
        cmd2 = exe_file_path + ' --rbp CR0 -p'
        # print cmd2
        id_str = str(self.dtq_id_lineedit.text())
        result = os.system( cmd1 )
        if result != 0:
            self.browser.append(u"<font color=red>DTQ@UID:[%s] 烧写失败！" % id_str )
            logging.debug(u"DTQ@UID:[%s] 烧写失败！" % id_str )
            return

        result = os.system( cmd2 )
        if result != 0:
            self.browser.append(u"<font color=red>DTQ@UID:[%s] 烧写失败！" % id_str )
            logging.debug(u"DTQ@UID:[%s] 烧写失败！" % id_str )
            return

        self.browser.append(u"<font color=green>DTQ@UID:[%s] 烧写成功！" % id_str )
        logging.debug(u"DTQ@UID:[%s] 烧写成功！" % id_str )

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = QtqBurner()
    datburner.show()
    app.exec_()

