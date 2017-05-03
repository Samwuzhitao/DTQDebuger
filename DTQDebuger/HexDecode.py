
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import string

class HexDecode():
    def __init__(self):
        self.status      = 0
        self.cnt         = 0
        self.xor         = 0
        self.str         = ""
        self.ReviceFunSets           = {
            "10":self.message_show_cmd_10,"11":self.message_show_cmd_11,
            "12":self.message_show_cmd_12,"13":self.message_show_cmd_10,
            "20":self.message_show_cmd_20,"21":self.message_show_cmd_20,
            "22":self.message_show_cmd_22,"23":self.message_show_cmd_22,
            "24":self.message_show_cmd_22,"25":self.message_show_cmd_22,
            "26":self.message_show_cmd_26,"27":self.message_show_cmd_22,
            "28":self.message_show_cmd_22,"29":self.message_show_cmd_26,
            "2A":self.message_show_cmd_22,"2b":self.message_show_cmd_2b,
            "2C":self.message_show_cmd_2c,"2d":self.message_show_cmd_22,
            "2E":self.message_show_cmd_2e,"2F":self.message_show_cmd_2f,
            "30":self.message_show_cmd_30,"31":self.message_show_cmd_31,
            "40":self.message_show_cmd_22,
            "41":self.message_show_cmd_22,"42":self.message_show_cmd_26,
            "43":self.message_show_cmd_43,
            "A0":self.message_show_cmd_22,
            "E0":self.message_show_cmd_e0,
        }

    def r_machine(self,x):
        global hex_decode_show_style
        char = "%02X" % ord(x)
        #print char
        #print "status = %d" % self.status
        if self.status == 0:
            if char == "5C":
                self.str =  char
                self.status = 1
            return ""

        if self.status == 1:
            self.str = self.str + ' ' + char
            self.xor = self.xor ^ ord(x)
            self.status = 2
            self.cnt = 4
            return ""

        if self.status == 2:
            self.str = self.str + ' ' + char
            self.xor = self.xor ^ ord(x)
            self.cnt = self.cnt - 1
            if self.cnt == 0:
                self.status = 3
            return ""

        if self.status == 3:
            self.str = self.str + ' ' + char
            self.xor = self.xor ^ ord(x)
            if ord(x) == 0:
                self.status = 5
                return ""
            self.status = 4
            self.cnt = ord(x)
            #print "message len = ",ord(x)
            return ""

        if self.status == 4:
            self.str = self.str + ' ' + char
            self.xor = self.xor ^ ord(x)
            self.cnt = self.cnt - 1
            uart_current_cnt = self.cnt
            if uart_current_cnt == 0:
                self.status = 5
            return ""

        if self.status == 5:
            uart_cal_oxr = self.xor
            uart_cal_oxr = "%02X" % uart_cal_oxr
            #print "uart_revice_oxr =",char
            #print "xor_cal(x) =",uart_cal_oxr
            uart_oxr_cmp = cmp(uart_cal_oxr,char)
            if uart_oxr_cmp == 0:
                #self.str_add(char)
                self.str = self.str + ' ' + char
                self.status = 6
                self.xor = 0
            else:
                self.status = 0
                self.xor = 0
            return ""

        if self.status == 6:
            if char == "CA":
                self.str = self.str + ' ' + char
                self.status = 0
                self.xor = 0
                # uart xor data ok
                #print self.str
                if hex_decode_show_style == 0:
                    self.str = " " + self.str
                    return self.str
                if hex_decode_show_style == 1:
                    self.str = self.message_show(self.str)
                    #cmd_type = str[4:6]
                    #self.ReviceFunSets[cmd_type](len_int,data,self.show)
                    return self.str
            return ""

    def message_show(self,str):
        str = " " + str
        cmd_type = str[4:6]
        sign_str = str[7:18]
        len_str  = str[19:21]
        len_int  = string.atoi(len_str, 16)
        #print len_int
        data     = str[22:22+len_int*3]
        xor      = str[22+len_int*3:22+len_int*3+2]
        end      = str[22+(len_int+1)*3:22+(len_int+1)*3+2]
        show_str = self.ReviceFunSets[cmd_type](len_int,data)

        return show_str

    def message_status_check(self,str):
        status = string.atoi(str, 10)
        if status == 0:
            str1 = " OK"
        else:
            str1 = " FAIL"
        return str1

    def message_status_check1(self,str):
        status = string.atoi(str, 10)
        if status == 0:
            str1 = " OK"
        else:
            str1 = " BUSY"
        return str1

    def message_process_show(self,x):
        if x == 1:
            show_str = "First Statistic:"
        if x == 2:
            show_str = "Second Statistic:"
        if x == 3:
            show_str = "Third Statistic:"
        if x == 4:
            show_str = "Fourth Statistic:"
        return show_str

    def message_show_cmd_10(self,len,str):
        show_str = message_status_check1(str[0:2])
        show_str += " WL_FILTER_STATUS = "+str[3:5]
        uidlen   = string.atoi(str[6:8],16)
        show_str += " WL_LEN = %d" % uidlen
        return show_str

    def message_show_cmd_11(self,len,str):
        show_str = ' Message : ' + str
        return show_str

    def message_show_cmd_12(self,len,str):
        show_str = message_status_check1(str[0:2])
        show_str += " WL_FILTER_STATUS = "+str[3:5]
        uidlen   = string.atoi(str[6:8],16)
        show_str += " WL_LEN = %d" % uidlen
        return show_str

    def message_show_cmd_20(self,len,str):
        uidlen   = string.atoi(str[0:2],16)
        show_str = " WL_OK_COUNT = %d" % uidlen
        uidlen   = string.atoi(str[27:29],16)
        show_str += " WL_LEN = %d" % uidlen
        show_str += " WL_DETAIL = "+str[3:26]
        return show_str

    def message_show_cmd_22(self,len,str):
        show_str = self.message_status_check(str[0:2])
        return show_str

    def message_show_cmd_26(self,len,str):
        uid = str[3:14]
        uid = uid.replace(' ','')
        show_str  = ' uPOS:[%3d] ' % string.atoi(str[0:2], 16)
        show_str += 'uID:[' + uid + ']'  + " Student ID:" + str[15:]
        return show_str

    def message_show_cmd_2b(self,len,str):
        global uidshowindex
        global uidshowflg
        global store_uid_switch
        global uid_table_first_write

        store_uid_switch = 1
        uidlen   = string.atoi(str[0:2],16)
        show_str = " uID SUM : %d " % uidlen
        #show_f(show_str,'a')

        if uidshowflg == 0:
            uidshowindex = 0
            uidshowflg   = 1

        i = 0
        j = 0
        show_str = " "

        while i < len :
            uid = str[(i+1)*3:(i+6)*3-1]
            uid = uid.replace(' ','')
            i = i + 5
            if uid != "":
                show_str     += "[%3d].%s " % (string.atoi(uid[0:2],16),uid[2:])
                uidshowindex = uidshowindex + 1
                j = j + 1
            if j == UID_SHOW_COL_NUM:
                j = 0
                store_uid_switch = 0
                uid_table_first_write = 0
                return show_str
            if i >= len :
                store_uid_switch = 0
                uid_table_first_write = 0
                return show_str

    def message_show_cmd_2c(self,len,str):
        #print "message_show_cmd_2c"
        uid       = str[0:11]
        show_str  = " ID  = "+uid.replace(' ','')
        #show_f(show_str,'a')
        sw_verion = str[12:20]
        sw_verion = sw_verion.replace(' ','')
        sw1 = string.atoi(sw_verion[0:2], 10)
        sw2 = string.atoi(sw_verion[3:4], 10)
        sw3 = string.atoi(sw_verion[5:6], 10)
        show_str  += " SW  = %d.%d%d" % (sw1,sw2,sw3)
        #show_f(show_str,'a')
        hwstr = str[21:65]
        hwstr = hwstr.replace(' ','')
        hwstr = hwstr.decode("hex")
        show_str  += " HW  = "+hwstr
        #show_f(show_str,'a')
        comstr = str[66:]
        comstr = comstr.replace(' ','')
        comstr = comstr.decode("hex")
        show_str  += " COM = "+"ZKXLTEACH"
        #print show_str
        return show_str

    def message_show_cmd_2d(self,len,str):
        #print "message_show_cmd_2d"
        i = 0
        while i < len :
            uid      = str[(i)*3:(i+4)*3-1]
            show_str = " online uid %2d : %s " % (i/4,uid)
            #show_f(show_str,'a')
            i = i + 4
        return show_str

    def message_show_cmd_2e(self,len,str):
        #print "message_show_cmd_2e"
        str = str.replace(' ','')
        show_str = " Src uid :"+str
        return show_str

    def message_show_cmd_2f(self,len,str):
        #print "message_show_cmd_2f"
        return message_status_check(str[0:2])

    def message_show_cmd_30(self,len,str):
        show_str = "lost:"
        show_f(show_str,'a')
        i = 1
        j = 0
        show_str = ""
        while i < len-3 :
            uid = str[(i)*3:(i+5)*3-1]
            uid = uid.replace(' ','')
            i = i + 5
            show_str += "[%3d].%s " % (string.atoi(uid[0:2], 16),uid[2:])
            j = j + 1
            if j == 5 :
                j = 0
                show_f(show_str,'a')
                show_str = ""
            if i >= len-3 :
                show_f(show_str,'a')
                show_str = ""
        show_str = "count:%d" % (len/5)
        return show_str

    def message_show_cmd_31(self,len,str):
        show_str = "Ok:"
        show_f(show_str,'a')
        i = 1
        j = 0
        show_str = ""
        while i < len - 3:
            uid = str[(i)*3:(i+5)*3-1]
            uid = uid.replace(' ','')
            i = i + 5
            show_str += "[%3d].%s " % (string.atoi(uid[0:2], 16),uid[2:])
            j = j + 1
            if j == 5 :
                j = 0
                show_f(show_str,'a')
                show_str = ""
            if i >= len-3 :
                show_f(show_str,'a')
                show_str = ""

        show_str = "count:%d" % (len/5)
        #show_f(show_str,'a')
        return show_str

    def message_show_cmd_43(self,len,str):
        #print "message_show_cmd_30"
        show_str = " Online uID:"
        show_f(show_str,'a')
        i = 0
        j = 0
        show_str = ""
        while i < len-3 :
            uid = str[(i)*3:(i+5)*3-1]
            uid = uid.replace(' ','')
            i = i + 5
            show_str += "[%3d].%s " % (string.atoi(uid[0:2], 16),uid[2:])
            j = j + 1
            if j == 5 :
                j = 0
                show_f(show_str,'a')
                show_str = ""
            if i >= len-3 :
                show_f(show_str,'a')
                show_str = ""
        show_str = "count:%d" % (len/5)
        #show_f(show_str,'a')
        return show_str

    def message_show_cmd_e0(self,len,str):
        #print "message_show_cmd_fd"
        show_str = message_status_check1(str[0:2])
        show_str += " err cmd = "+str[0:2] + " err code = "+str[3:]
        return show_str