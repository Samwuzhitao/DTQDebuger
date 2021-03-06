# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import serial
import string
import time
import os
import subprocess
import sys
import logging
import json
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from JsonDecode   import *

ser           = 0
input_count   = 0
LOGTIMEFORMAT = '%Y%m%d%H'
log_time      = time.strftime( LOGTIMEFORMAT,time.localtime(time.time()))
log_name      = "log-%s.txt" % log_time

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = log_name,
    filemode = 'w',
    format = u'【%(asctime)s】 %(message)s',
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
            recv_str = str1
        return recv_str

    def run(self):
        global ser
        global input_count

        while self.working==True:
            if input_count   >= 1:
                recv_str      = None
                try:
                    read_char = ser.read(1)
                except serial.SerialException:
                    input_count = 0
                    cmd = u'{"fun":"Error","description":"serialport lost!"}'
                    recv_str = cmd
                    pass
                if input_count > 0:
                    recv_str  = self.ReviceFunSets[0]( read_char )
                if recv_str :
                    print recv_str
                    self.emit(SIGNAL('output(QString)'),recv_str)

class LogResult():
    def __init__(self, parent=None):
        self.burn_sum_count  = 0
        self.card_ok_count   = 0
        self.card_fail_count = 0
        self.rssi_ok_count   = 0
        self.rssi_fail_count = 0

    def clear(self):
        self.burn_sum_count  = 0
        self.card_ok_count   = 0
        self.card_fail_count = 0
        self.rssi_ok_count   = 0
        self.rssi_fail_count = 0

class QtqBurner(QWidget):
    def __init__(self, parent=None):
        global ser

        super(QtqBurner, self).__init__(parent)
        input_count         = 0
        self.device_type    = ""
        self.logresult      = LogResult()
        self.ports_dict     = {}
        self.dtq_image_path = ''
        self.new_image_path = ''
        self.dtq_id         = ''
        self.pro_dict       = {
            u'ZKXL'    :u'中科讯联（我司）',
            u'JXYD'    :u'江西移动',
            u'CQYD'    :u'重庆移动',
            u'NMYD'    :u'内蒙移动',
            u'GXYDCG'  :u'广西移动(初稿)',
            u'GXYDDG'  :u'广西移动(定稿)',
            u'GZYD'    :u'贵州移动',
            u'GSYD'    :u'甘肃移动',
            u'SXYDTB'  :u'山西移动_天波',
            u'SXYDXN'  :u'山西移动_鑫诺',
            u'SXYDTYXY':u'山西移动_统一协议',
            u'AHYD'    :u'安徽移动',
            u'SCYD'    :u'四川移动',
            u'ZKXL_YJLKQ':u'中科讯联:远距离考勤'
        }
        self.CmdFunSets = {
            "update_card_info" :self.update_card_info,
            "card_setting"     :self.card_setting,
            "rssi_check"       :self.rssi_check,
            "si24r2e_auto_burn":self.si24r2e_auto_burn,
            "bind_start"       :self.bind_start,
            "Error"            :self.Error,
            "debug"            :self.debug,
            "nvm_opration"     :self.nvm_opration,
            "si24r2e_show_log" :self.show_log,
            "system_init"      :self.system_init
        }
        self.current_cmd = ''
        self.setWindowTitle(u"烧录工具v0.1.4")

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
        self.boot_button  = QPushButton(u"添加固件")
        self.boot_browser = QLineEdit()
        self.boot_label=QLabel(u"镜像文件:")
        self.save_button  = QPushButton(u"转换文件")
        self.burn_button = QPushButton(u"烧录")
        dtq_layout = QHBoxLayout()
        dtq_layout.addWidget(self.boot_label)
        dtq_layout.addWidget(self.boot_browser)
        dtq_layout.addWidget(self.boot_button)
        dtq_layout.addWidget(self.save_button)
        dtq_layout.addWidget(self.burn_button)

        self.yyk_wiget = QWidget()
        self.pro_lineedit = QLineEdit()
        self.pro_label = QLabel(u"当前协议:")
        self.burn_count_lineedit = QLineEdit()
        self.burn_count_lineedit.setFixedSize(40, 20)
        self.burn_count_label = QLabel(u"编程次数:")
        self.pro_label.setFixedSize(60, 20)
        self.pro_button = QPushButton(u"开始烧录")
        self.debug_button = QPushButton(u"打开调试信息")
        self.version_label = QLabel(u"固件版本:")
        self.version_lineedit = QLineEdit()
        self.version_lineedit.setFixedSize(40, 20)
        yyk_layout = QHBoxLayout()
        yyk_layout.addWidget(self.pro_label)
        yyk_layout.addWidget(self.pro_lineedit)
        yyk_layout.addWidget(self.burn_count_label)
        yyk_layout.addWidget(self.burn_count_lineedit)
        yyk_layout.addWidget(self.version_label)
        yyk_layout.addWidget(self.version_lineedit)
        yyk_layout.addWidget(self.pro_button)
        yyk_layout.addWidget(self.debug_button)

        self.dtq_wiget.setLayout(dtq_layout)
        self.yyk_wiget.setLayout(yyk_layout)

        self.dtq_tabwidget.addTab(self.dtq_wiget, u"&DTQ")
        self.dtq_tabwidget.addTab(self.yyk_wiget, u"&YYK")

        self.browser = QTextBrowser()
        self.browser.setFont(QFont("Courier New", 10, QFont.Bold))
        self.browser.document().setMaximumBlockCount (10000);

        vbox = QVBoxLayout()
        vbox.addWidget(self.dtq_tabwidget)
        vbox.addWidget(self.browser)

        box = QVBoxLayout()
        box.addLayout(c_hbox)
        box.addLayout(e_hbox)
        box.addLayout(vbox)
        self.setLayout(box)
        self.resize( 630, 500 )

        self.boot_button.clicked.connect(self.choose_image_file)
        self.burn_button.clicked.connect(self.download_image)
        self.clear_button.clicked.connect(self.clear_text)
        self.pro_button.clicked.connect(self.yyk_update_pro)
        self.debug_button.clicked.connect(self.yyk_debug)

        self.start_button.clicked.connect(self.band_start)
        self.save_button.clicked.connect(self.exchange_file)
        self.uart_listen_thread=UartListen()
        self.connect(self.uart_listen_thread,SIGNAL('output(QString)'),
            self.uart_update_text)
        self.com_combo.currentIndexChanged.connect(self.change_uart)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def keyPressEvent(self, e):
        print e.key()
        if e.key() == 16777220: # Enter键
            self.download_image()

    def send_cmd(self,cmd):
        global ser
        global input_count

        ser.write(cmd)
        input_count = input_count + 1
        self.current_cmd = cmd

    def re_send_cmd(self):
        ser.write(self.current_cmd)

    def update_card_info(self,json_dict):
        self.dtq_id = json_dict[u"card_id"]
        self.dtq_id_lineedit.setText(self.dtq_id)
        self.exchange_file()

    def card_setting(self,json_dict):
        self.device_type = "YYK"
        if json_dict.has_key(u"result") == True:
            result = json_dict[u"result"]
            pro_name = json_dict[u"pro_name"]
            self.dtq_id = json_dict[u"card_id"]
            self.dtq_id_lineedit.setText(self.dtq_id)
            show_str = ""
            if result == u"0":
                show_str = u"<font color=black>%s@UID:[%s] CARD_SET  :成功！\
                </font>" % (pro_name,self.dtq_id)
                self.browser.append(show_str)
                logging.debug( u"%s@UID:[%s] CARD_SET  :成功！" % (pro_name,self.dtq_id) )
                self.logresult.card_ok_count = self.logresult.card_ok_count + 1
            else:
                self.logresult.card_fail_count = self.logresult.card_fail_count + 1
            if result == u"-1":
                show_str = u"<font color=black>%s@UID:[%s] CARD_SET  :</font><font \
                color=red>失败！失败类型：烧写失败!</font>" % (pro_name,self.dtq_id)
                self.browser.append(show_str)
                logging.debug( u"%s@UID:[%s] CARD_SET  :失败！失败类型：烧写失败!" % (pro_name,self.dtq_id))
            if result == u"-2":
                show_str = u"<font color=black>%s@UID:[%s] CARD_SET  :</font><font \
                color=red>失败！失败类型：烧写次数满</font>" % (pro_name,self.dtq_id)
                self.browser.append(show_str)
                logging.debug( u"%s@UID:[%s] CARD_SET  :失败！失败类型：烧写次数满!" % (pro_name,self.dtq_id))
            if result == u"-3":
                show_str = u"<font color=black>%s@UID:[%s] CARD_SET  :</font><font \
                color=red>失败！失败类型：管脚松动</font>" % (pro_name,self.dtq_id)
                self.browser.append(show_str)
                logging.debug( u"%s@UID:[%s] CARD_SET  :失败！失败类型：管脚松动!" % (pro_name,self.dtq_id))
            self.logresult.burn_sum_count = self.logresult.burn_sum_count + 1

    def rssi_check(self,json_dict):
        if json_dict.has_key(u"result") == True:
            result = json_dict[u"result"]
            rssi   = json_dict[u"check_rssi"]
            self.dtq_id = json_dict[u"card_id"]
            pro_name = json_dict[u"pro_name"]
            show_str = ""
            if self.dtq_id == u"0000000000" or self.dtq_id == u"ffffffffff":
                show_str = u"<font color=black>%s@RSSI_CHECK:</font>\
                <font color=red>失败!</font>" % (pro_name)
                self.logresult.rssi_fail_count = self.logresult.rssi_fail_count + 1
                self.browser.append(show_str)
            else:
                show_str = u"<font color=black>%s@UID:[%s] RSSI_CHECK:成功！\
                RSSI = %s</font>" % (pro_name,self.dtq_id,rssi)
                self.logresult.rssi_ok_count = self.logresult.rssi_ok_count + 1
                self.browser.append(show_str)
            result_str = u"ID:【%s】 RSSI: %s RSSI_CHECK:%s" %  (self.dtq_id,rssi,result)
            logging.debug(result_str)

    def si24r2e_auto_burn(self,json_dict):
        if json_dict.has_key(u"result") == True:
            result   = json_dict[u"result"]
            pro_name = json_dict[u"pro_name"]
            setting  = json_dict[u"setting"]
            debug    = json_dict[u"debug"]
            version  = json_dict[u"version"]
            op = u''
            if json_dict.has_key(u"version") == True:
                version = json_dict[u"version"]
                self.version_lineedit.setText(version)
            if result == u"0":
                if self.pro_dict.has_key(pro_name) == True:
                    self.pro_lineedit.setText(self.pro_dict[pro_name])
                if setting == u"start":
                    op = u'开始烧录'
                    self.pro_button.setText(u'停止烧录')
                if setting == u"stop":
                    op = u'停止烧录'
                    self.pro_button.setText(u'开始烧录')
                self.browser.append(u"<font color=black>当前协议:[%s] 固件版本:[%s] \
                    烧录设置成功，%s!</font>" % (pro_name,version,op) )
                logging.debug(u"设置协议:[%s] 成功，%s!" % (pro_name,op) )

                if debug == u'0':
                    self.debug_button.setText(u"打开调试信息")
                else:
                    self.debug_button.setText(u"关闭调试信息")
            else:
                self.browser.append(u"<font color=black>%s@设置协议:[%s]</font>\
                    <font color=red>失败!</font>" % pro_name )
                logging.debug(u"设置协议:[%s] 失败!" % pro_name )

    def bind_start(self,json_dict):
        if json_dict.has_key(u"device_type") == True:
            device_type = json_dict[u"device_type"]
            if self.dtq_tabwidget.count() == 2:
                if device_type == "DTQ":
                    self.dtq_tabwidget.removeTab(1)
                if device_type == "YYK":
                    self.dtq_tabwidget.removeTab(0)

        if json_dict.has_key(u"result") == True:
            result = json_dict[u"result"]
            if result == u"0":
                self.browser.append(u"<font color=black>打开串口!</font>" )
                logging.debug(u"打开串口!" )

    def nvm_opration(self,json_dict):
        if json_dict.has_key(u"operation") == True:
            operation = json_dict[u"operation"]
            show_str = ""
            if json_dict.has_key(u"read_nvm_data") == True:
                read_nvm_data = json_dict[u"read_nvm_data"]
                read_burn_count = json_dict[u"read_burn_count"]
                show_str = u"读出配置：burn_count：%s read_data:%s" % \
                (read_burn_count,read_nvm_data )
                self.browser.append("<font color=black>%s</font>" % show_str)
                logging.debug( show_str )
            if operation == u"wr":
                show_str = u"比较配置不一致,重新写入配置"
                self.browser.append("<font color=black>%s</font>" % show_str)
                logging.debug( show_str )

        if json_dict.has_key(u"read_burn_count") == True:
            read_burn_count = json_dict[u"read_burn_count"]
            self.burn_count_lineedit.setText(read_burn_count)

    def Error(self,json_dict):
        if json_dict.has_key(u"description") == True:
            result = json_dict[u"description"]
            if result == "json syntax error!" or "unknow cmd!":
                self.re_send_cmd()
            else:
                self.browser.append(u"错误类型:%s" % result )
            logging.debug(u"错误类型:%s" % result )

            if result == "serialport lost!":
                self.start_button.setText(u"打开接收器")
                self.pro_button.setText(u"开始烧录")
                self.debug_button.setText(u"打开调试信息")
                self.burn_count_lineedit.setText(u'')
                self.show_log_result()

    def debug(self,json_dict):
        data = json.dumps(json_dict)
        self.browser.append("<font color=black>%s</font>" % data)
        logging.debug( data )

    def show_log(self,json_dict):
        if json_dict.has_key(u"result") == True:
            result = json_dict[u"result"]
            if result == u"0":
                self.browser.append(u"<font color=black>调试信息设置成功!</font>")
                logging.debug(u"调试信息设置成功!" )

    def yyk_debug(self):
        global ser
        global input_count

        if input_count   >= 1:
            button = self.sender()

            if button is None or not isinstance(button, QPushButton):
                return
            button_str = button.text()

            if button_str == u"打开调试信息":
                self.debug_button.setText(u"关闭调试信息")
                cmd = '{"fun":"si24r2e_show_log","setting": "1"}'
            if button_str == u"关闭调试信息":
                self.debug_button.setText(u"打开调试信息")
                cmd = '{"fun":"si24r2e_show_log","setting": "0"}'

            if ser.isOpen() == True:
                self.send_cmd(cmd)
            return

    def yyk_update_pro(self):
        global ser
        global input_count

        if input_count   >= 1:
            ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'
            now = time.strftime( ISOTIMEFORMAT,time.localtime(time.time()))
            button = self.sender()

            button_str = self.pro_button.text()

            if button_str == u"开始烧录":
                if ser.isOpen() == True:
                    cmd = '{"fun": "si24r2e_auto_burn","setting": "1","time": "%s"}' % now
                    ser.write(cmd)
                    input_count = input_count + 1
                    data = u"S[%d]: " % (input_count-1) + u"%s" % cmd
                return

            if button_str == u"停止烧录":
                self.burn_count_lineedit.setText(u'')
                self.show_log_result()

                if ser.isOpen() == True:
                    cmd = '{"fun": "si24r2e_auto_burn","setting": "0","time": "%s"}' % now
                    self.send_cmd(cmd)
                    data = u"S[%d]: " % (input_count-1) + u"%s" % cmd
                return

    def system_init(self,json_dict):
        if json_dict.has_key(u"status") == True:
            status = json_dict[u"status"]
            self.start_button.setText(u"打开接收器")
            self.pro_button.setText(u"开始烧录")
            self.debug_button.setText(u"打开调试信息")
            self.burn_count_lineedit.setText(u'')
            input_count = 0
            self.browser.append(u"系统初始化，初始化结果:%s" % status )
            logging.debug(u"系统初始化，初始化结果:%s" % status )

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
        print data
        json_dict = {}
        try:
            json_dict = json.loads(str(data))
        except ValueError:
            pass
        print json_dict

        if json_dict.has_key(u"fun") == True:
            fun = json_dict[u"fun"]
            if self.CmdFunSets.has_key(fun) == True:
                self.CmdFunSets[fun](json_dict)
            else:
                self.browser.append(u"未识别指令:%s" % fun )
                logging.debug(u"未识别指令:%s" % fun )
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

    def setting_uart(self,mode):
        global ser
        global input_count

        serial_port = str(self.com_combo.currentText())

        try:
            ser = serial.Serial( self.ports_dict[serial_port], 1152000)
        except serial.SerialException:
            pass

        if mode == 1:
            if ser.isOpen() == True:
                self.start_button.setText(u"关闭接收器")
                self.uart_listen_thread.start()
                input_count = input_count + 1
        else:
            self.start_button.setText(u"打开接收器")
            self.pro_button.setText(u"开始烧录")
            self.debug_button.setText(u"打开调试信息")
            self.burn_count_lineedit.setText(u'')
            input_count = 0
            ser.close()

    def exchange_file(self):
        #print "****"
        if self.dtq_image_path :
            f = open(self.dtq_image_path)
            li = f.readlines()
            f.close()

            time_data = time.strftime( '%Y%m%d',time.localtime(time.time()))
            uid_str   = "%08X" % (string.atoi(str(self.dtq_id_lineedit.text()),10))
            insert_data = "08FC0000" + time_data + uid_str
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

            self.browser.append(u"<font color=black>DTQ@UID:[%s] HEX文件转换成功</font>" %
                str(self.dtq_id_lineedit.text()) )
        else:
            self.browser.append(u"<font color=black>DTQ@错误:</font><font color=red>无烧写固件</font>")

    def band_start(self):
        global ser
        global input_count

        button = self.sender()
        button_str = button.text()

        if button_str == u"打开接收器":
            self.setting_uart(1)
            if ser.isOpen() == True:
                self.uart_listen_thread.start()
                cmd = "{'fun':'bind_start'}"
                self.send_cmd(cmd)
                data = u"S[%d]: " % (input_count-1) + u"%s" % cmd
                return

        if button_str == u"关闭接收器":
            if input_count >= 1:
                cmd = '{"fun": "si24r2e_auto_burn","setting": "0"}'
                self.send_cmd(cmd)
                self.setting_uart(0)
                self.browser.append(u"关闭串口!" )
                logging.debug(u"关闭串口!" )
                self.show_log_result()
                return
            else:
                self.setting_uart(0)

    def choose_image_file(self):
        button = self.sender()

        if button is None or not isinstance(button, QPushButton):
            return
        #print "clicked button is %s " % button.text()
        button_str = button.text()

        if button_str == u"添加固件":
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
        result = 0
        id_str = str(self.dtq_id_lineedit.text())
        cmd1 = cmd1.encode("gbk")
        ps = subprocess.Popen( cmd1 )
        ps.wait()
        result =  ps.returncode

        if result != 0:
            self.browser.append(u"<font color=black>DTQ@UID:[%s] </font>\
                <font color=red>烧写失败!</font>" % id_str )
            logging.debug(u"DTQ@UID:[%s] 烧写失败！" % id_str )
            return

        ps = subprocess.Popen( cmd2 )
        cmd2 = cmd2.encode("gbk")
        ps.wait()
        result =  ps.returncode
        if result != 0:
            self.browser.append(u"<font color=black>DTQ@UID:[%s] </font>\
                <font color=red>烧写失败!</font>" % id_str )
            logging.debug(u"DTQ@UID:[%s] 烧写失败！" % id_str )
            return

        self.browser.append(u"<font color=black>DTQ@UID:[%s] 烧写成功</font>" % id_str )
        logging.debug(u"DTQ@UID:[%s] 烧写成功！" % id_str )

    def show_log_result(self):
        if self.device_type == "YYK":
            show_str = u"============================================================"
            logging.debug( show_str )
            self.browser.append("<font color=black>%s</font>" % show_str)
            show_str = u"烧录结果统计:"
            logging.debug( show_str )
            self.browser.append("<font color=black>%s</font>" % show_str)
            show_str = u"总共烧录次数:%d" % datburner.logresult.burn_sum_count
            logging.debug( show_str )
            self.browser.append("<font color=black>%s</font>" % show_str)
            show_str = u"CARD配置结果:成功=%-10d 失败=%-10d"  % (datburner.logresult.card_ok_count,\
                                                             datburner.logresult.card_fail_count )
            logging.debug( show_str )
            self.browser.append("<font color=black>%s</font>" % show_str)
            show_str = u"RSSI检验结果:成功=%-10d 失败=%-10d"  % (datburner.logresult.rssi_ok_count,\
                                                         datburner.logresult.rssi_fail_count )
            logging.debug( show_str )
            self.browser.append("<font color=black>%s</font>" % show_str)
            show_str = u"============================================================"
            logging.debug( show_str )
            self.browser.append("<font color=black>%s</font>" % show_str)


if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = QtqBurner()
    datburner.show()
    sys.exit(app.exec_())
    cmd = '{"fun": "si24r2e_auto_burn","setting": "0"}'
    if ser != 0:
        try:
            datburner.send_cmd(cmd)
        except serial.SerialException:
            pass
        datburner.setting_uart(0)
        datburner.show_log_result()



