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
import datetime
from cmd_rev_decode import *
from com_monitor    import *

ser           = 0
input_count   = 0
LOGTIMEFORMAT = '%Y%m%d%H'
ISOTIMEFORMAT = '%Y-%m-%d %H:%M:%S'
log_time      = time.strftime( LOGTIMEFORMAT,time.localtime(time.time()))
log_name      = "log-%s.txt" % log_time
CONF_FONT_SIZE = 16
DIS_NOP = '--'

logging.basicConfig ( # 配置日志输出的方式及格式
    level = logging.DEBUG,
    filename = log_name,
    filemode = 'a',
    format = u'[%(asctime)s] %(message)s',
)

class DTQMonitor(QObject):
    def __init__(self,parent=None):
        super(DTQMonitor,self).__init__(parent)
        self.ser_list     = []
        self.monitor_dict = {}
        self.ser          = None
        self.ComMonitor   = None
        self.dtq_id       = ''
        self.jsq_id       = ''
        self.start_time   = 0
        self.end_time     = 0
        self.uid_list     = []
        self.uid_sict     = {}
        self.data_type_dict = {'00':u'DATA','01':u'ACK ','02':u'PRE '}
        self.holk_fun    = None

    def exchang_uid_hex_to_dec(self,uid):
        new_uid = uid[6:8] + uid[4:6] + uid[2:4] + uid[0:2]
        return string.atoi(new_uid,16)


    def uart_cmd_decode(self,data):
        data = str(data)
        # 回复ACK
        data_type  = ''
        restlt_str = ''

        try:
            data_type = self.data_type_dict[data[4:6]]
        except KeyError:
            return
        src_uid = data[6:14]
        dst_uid = data[14:14+8]
        seq_id  = data[14+8:14+10]
        pac_id  = data[14+10:14+12]
        logic_id = data[14+12:14+14]

        # # 解析读取UID指令对应的返回
        if data[2:4] == '0C':
            if src_uid == self.jsq_id:
                if dst_uid not in self.uid_list:
                    self.uid_list.append( dst_uid )
                    self.uid_sict[dst_uid] = len(self.uid_list)
                restlt_str = '[%10d] ' % self.exchang_uid_hex_to_dec(src_uid) + DIS_NOP + '%s' % data_type + \
                              DIS_NOP*self.uid_sict[dst_uid] + '>' + ' [%10d] ' % self.exchang_uid_hex_to_dec(dst_uid)
            else:
                if src_uid not in self.uid_list:
                    self.uid_list.append( src_uid )
                    self.uid_sict[src_uid] = len(self.uid_list)
                restlt_str = '[%10d] ' % self.exchang_uid_hex_to_dec(dst_uid) + '<' + DIS_NOP + '%s' % data_type + \
                              DIS_NOP*self.uid_sict[src_uid] + ' [%10d] ' % self.exchang_uid_hex_to_dec(src_uid)

            restlt_str = 'seq:%s ' % seq_id + 'pac:%s ' % pac_id + restlt_str
        logging.debug( u"%s" % restlt_str)
        if self.hook_fun:
            now = time.strftime( ISOTIMEFORMAT,time.localtime(time.time()))
            ms  = datetime.datetime.now().microsecond
            self.hook_fun('[%s,%03d]:' % (now,ms/1000) + restlt_str)

    def config_id_update(self,dev_id):
        self.jsq_id   = dev_id#'2F53D40B'

    def config_data_update(self,hook_fun):
        self.ser_list = ['COM6','COM43']
        self.jsq_id   = '7C23DDAC'#'2F53D40B'
        self.hook_fun = hook_fun

        print self.ser_list
        i = 0
        for item in self.ser_list:
            ser = None
            i = i + 1
            try:
                ser = serial.Serial( item, 1000000)
            except serial.SerialException:
                QMessageBox.critical(self,u"错误",u"创建 标签%d:%s 监听线程失败! " % (i,item))
                pass
            if ser:
                self.monitor_dict[item] = ComMonitor(ser)
                print u"启动串口监听线程! %s " % item
                self.connect( self.monitor_dict[item],
                        SIGNAL('r_cmd_message(QString)'),self.uart_cmd_decode)
                self.monitor_dict[item].start()

if __name__=='__main__':
    app = QApplication(sys.argv)
    datburner = DTQMonitor()
    datburner.config_data_update(None)
    app.exec_()