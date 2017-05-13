
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 22 10:59:35 2017

@author: Samwu
"""
import serial
import string
from PyQt4.QtCore import *
from PyQt4.QtGui  import *

class COMSetting(QDialog):
    def __init__(self, parent=None):
        super(COMSetting, self).__init__(parent)
        self.ports_dict    = {}
        self.ser = None
        self.setWindowTitle(u'连接管理')
        self.com_combo=QComboBox(self) 
        self.com_combo.setFixedSize(75, 20)
        self.uart_scan()

        self.open_com_button=QPushButton(u"打开串口")
        self.open_com_button.setFixedSize(75, 20) 

        self.baudrate_label=QLabel(u"波特率：") 
        self.baudrate_label.setFixedSize(60, 20)
        self.baudrate_lineedit = QLineEdit(u'1152000')
        self.baudrate_lineedit.setFixedSize(50, 20)
        self.baudrate_unit_label=QLabel(u"bps ") 
        self.baudrate_unit_label.setFixedSize(20, 20)
        
        c_hbox = QHBoxLayout()
        c_hbox.addWidget(self.com_combo)
        c_hbox.addWidget(self.open_com_button)
        c_hbox.addWidget(self.baudrate_label)
        c_hbox.addWidget(self.baudrate_lineedit)
        c_hbox.addWidget(self.baudrate_unit_label)

        self.setLayout(c_hbox)

        self.open_com_button.clicked.connect(self.open_uart)

    def uart_scan(self):
        for i in range(256):
            
            try:
                s = serial.Serial(i)
                self.com_combo.addItem(s.portstr)
                self.ports_dict[s.portstr] = i
                s.close()
            except serial.SerialException:
                pass
    def open_uart(self):

        serial_port = str(self.com_combo.currentText())
        baud_rate   = str(self.baudrate_lineedit.text())

        button = self.sender()

        if button is None or not isinstance(button, QPushButton):
            return
        #print "clicked button is %s " % button.text()
        button_str = button.text()

        if button_str == u"打开串口":
            try:
                self.ser = serial.Serial( self.ports_dict[serial_port], 
                    string.atoi(baud_rate, 10))
            except serial.SerialException: 
                pass
            if self.ser :
                if self.ser.isOpen() == True:
                    self.open_com_button.setText(u"关闭串口")
            else:
                return 
        else:
                self.open_com_button.setText(u"打开串口")
                self.ser.close()
    
    @staticmethod
    def get_port(parent = None):
        comsetting_dialog = COMSetting(parent)
        result = comsetting_dialog.exec_()

        return (comsetting_dialog.ser)