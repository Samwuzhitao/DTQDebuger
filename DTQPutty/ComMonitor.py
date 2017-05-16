# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: Samwu
"""
import string
from PyQt4.QtCore import *
from PyQt4.QtGui  import *

from JsonDecode import *
from HexDecode  import *
from BinDecode  import *

class ComMonitor(QThread):
    def __init__(self,com,parent=None):
        super(ComMonitor,self).__init__(parent)
        self.working  = True
        self.num      = 0
        self.com      = com
        # print self.com
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