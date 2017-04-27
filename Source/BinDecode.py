
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

    def encode_header_package(self,file_name,file_size):
        NOP  = 0
        data = "%s %d" % (file_name,file_size)

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

        self.pack_num = self.pack_num + 1
        self.pack_cmd = self.pack_cmd + 1

        return self.package

    def encode_data_package(self,data):
        self.pack_num = self.pack_num + 1

        print self.pack_num


    def send_package(self):
        print "send"

    def run(self):
        data_path  = os.path.abspath("./") +'\\data\\'
        image_path = data_path + 'DTQ_RP551CPU_ZKXL0200_V0102.bin'
        size       = os.path.getsize(image_path)
        #print size
        f = open(image_path, "rb")

        send_index = 0
        count = 0
        DATA_LEN = 1024

        #发送文件名和长度
        self.encode_header_package(image_path,size)


        while( size > send_index ):
            #print count
            #print "read_start = %d " % (send_index)
            f.seek(send_index,0)

            if (send_index + DATA_LEN) < size:
                read_count = DATA_LEN
            else:
                read_count = size-send_index

            temp=f.read(read_count) 
            send_index = send_index + read_count

            u8_array  = [string.atoi(item.encode('hex'), 16) for item in temp]
            #for i in u8_array:
            #    print  ",0x%02x" % i,
            #print ""
            crc16 = self.cal_crc16(u8_array)
            count = count + 1
            #print "read_count = %03d crc16 = %04x" % (count,crc16)


        f.close()
