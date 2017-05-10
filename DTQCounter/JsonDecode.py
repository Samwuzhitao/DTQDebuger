
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: john
"""
import string

class JsonDecode():
    def __init__(self):
        self.status      = 0
        self.cnt         = 0
        self.str         = ""

    def r_machine(self,x):
        char = x
        #print "status = %d cnt = %d str: %s" % (self.status,self.cnt,self.str)

        # revice header
        if self.status == 0:
            self.str = ""
            if char == '{':
                self.str =  char
                self.cnt = self.cnt + 1
                self.status = 1
                return ""

        # revice data
        if self.status == 1:
            self.str = self.str + char
            if char == '{':
                self.cnt = self.cnt + 1
                return ""
            if char == '}':
                self.cnt = self.cnt - 1
                if self.cnt == 0:
                    #print self.str
                    self.status = 0
                    self.cnt    = 0
                    return self.str
                else:
                    return ""
        return ""