
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""

import string
import os
import sys

class BinDecode():
    def __init__(self): 
        self.package    = []
        self.pack_cmd   = 0
        self.pack_num   = 0
        self.pack_unnum = 0
        self.crc16      = 0
        self.image_path = ''
        self.file_size  = 0
        self.send_index = 0
        self.count      = 0
        self.DATA_LEN   = 1024
        self.over       = 0

    def update_crc16(self,crc_in,u8_data):
        crc_temp = crc_in
        data_in  = u8_data | 0x100

        while((data_in & 0x10000) == 0):
            crc_temp <<= 1
            data_in  <<= 1
            if (data_in & 0x100):
                crc_temp = crc_temp + 1
            if (crc_temp & 0x10000):
                crc_temp ^= 0x1021

        return (crc_temp & 0xFFFF)

    def cal_crc16(self,u8_data_array):
        crc = 0
        for i in u8_data_array:
            crc = self.update_crc16(crc,i)

        crc = self.update_crc16(crc,0)
        crc = self.update_crc16(crc,0)
        return (crc & 0xFFFF)

    def soh_pac(self,file_name,file_size):
        NOP  = 0
        data_path  = os.path.abspath("../") +'\\data\\'
        data = "%s %d" % (file_name,file_size)
        self.image_path = data_path + file_name
        self.file_size  = file_size

        self.package= []
        # 封装帧头
        self.pack_cmd = 1
        self.pack_num = 0
        self.pack_unnum = 0xFF
        self.package.append(self.pack_cmd)
        self.package.append(self.pack_num)
        self.package.append(self.pack_unnum)

        # 封装帧内容
        for item in data:
             self.package.append(ord(item))
        for i in range(128-len(data)):
            self.package.append(NOP)
        #计算CRC16
        self.crc16 = self.cal_crc16(self.package[3:])
        
        self.package.append(self.crc16 & 0xFF)
        self.package.append((self.crc16 & 0xFF00)>>8)

        return self.package

    def stx_pac(self):
        # 封装帧头
        NOP  = 0
        data = ''
        self.package= []
        self.pack_cmd = 2
        self.pack_num = self.count
        self.pack_unnum = self.count ^ 0xFF
        self.package.append(self.pack_cmd)
        self.package.append(self.pack_num)
        self.package.append(self.pack_unnum)

        # 封装帧内容
        # 读取数据
        f = open(self.image_path, "rb")
        if self.file_size > self.send_index :
            #print count
            #print "read_start = %d " % (send_index)
            f.seek(self.send_index,0)

            if (self.send_index + self.DATA_LEN) < self.file_size:
                read_count = self.DATA_LEN
            else:
                read_count = self.file_size-self.send_index

            data=f.read(read_count) 
            #print type(data)
            self.send_index = self.send_index + read_count
            self.count = self.count + 1
            #print "read_count = %03d crc16 = %04x" % (count,crc16)
        f.close()

        # 封装数据
        if len(data) > 0:
            for item in data:
                 self.package.append(ord(item))
        if len(data) < self.DATA_LEN:
            for i in range(self.DATA_LEN-len(data)):
                self.package.append(NOP)
        #计算CRC16
        self.crc16 = self.cal_crc16(self.package[3:])
        
        self.package.append(self.crc16 & 0xFF)
        self.package.append((self.crc16 & 0xFF00)>>8)

        return self.package
