'''
Created on 2019/04/11
@author: E9981231
'''
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication
from matplotlib.figure import Figure
import sys
import numpy as np
from dbc import dbc
from InternalCAN import *  #need adapt this name when changed DBC name
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from PyQt5.Qt import pyqtSignal

Scope_Window_File = "../UI/Scope.ui" 
DBC_NAME = "InternalCAN.py" #need adapt this name when changed DBC name
Ui_Scope, QtBaseClass = uic.loadUiType(Scope_Window_File)

CH1YArray = []
CH2YArray = []


class Scope_Window(QMainWindow,Ui_Scope):
    TrigSig = pyqtSignal()
    def __init__(self):
        super(Scope_Window,self).__init__()
        self.setupUi(self)
        self.fig = Figure()
        self.ax1f1 = self.fig.add_subplot(111)
#         self.ax1f1.set_autoscalex_on(False)
        self.canvas = FigureCanvas(self.fig)
        self.matplot_vlayout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas,
                                         self.matplot_widget, coordinates=True)
        self.matplot_vlayout.addWidget(self.toolbar)
        
        ''' Add signal name option into comboBox '''
#         for m in dbc[0].messages:
#             for s in m.signals:
#                 self.comboBox_CH1.addItem(s.name)
#                 self.comboBox_CH2.addItem(s.name)
        with open(DBC_NAME, 'r') as f:
            lines = f.read().split("\n")
            for line in lines:
                if line.strip() == "":
                    continue
                parts = line.split(" ")
                if parts[0][:5] == 'ID_0x' and "OBC" in parts[0]:
                    self.comboBox_CH1.addItem(parts[0])
                    self.comboBox_CH2.addItem(parts[0])
            pass
        
        ''' Init slider value'''
        self.CH1_verticalSlider.setMinimum(eval(self.comboBox_CH1.currentText()).minimum)
        self.CH1_verticalSlider.setMaximum(eval(self.comboBox_CH1.currentText()).maximum)
        self.CH2_verticalSlider.setMinimum(eval(self.comboBox_CH2.currentText()).minimum)
        self.CH2_verticalSlider.setMaximum(eval(self.comboBox_CH2.currentText()).maximum)
        
        self.ch1_wave = None
        self.ch2_wave = None
        self.interval = None
        self.points = 100
        self.ttt = 0
        self.TimeStopFlag = None
        
        #Banding
        self.comboBox_CH1.currentIndexChanged.connect(lambda: self.Slot_comboBox(1))
        self.comboBox_CH2.currentIndexChanged.connect(lambda: self.Slot_comboBox(2))
        self.CH1_verticalSlider.valueChanged.connect(lambda: self.Slot_Slider(1))
        self.CH2_verticalSlider.valueChanged.connect(lambda: self.Slot_Slider(2))
        self.Btn_Start.clicked.connect(self.Slot_Btn_Start)
       
    def Slot_comboBox(self, ch):
        if ch == 1:
            try:
                self.CH1_verticalSlider.setMinimum(eval(self.comboBox_CH1.currentText()).minimum)
                self.CH1_verticalSlider.setMaximum(eval(self.comboBox_CH1.currentText()).maximum)
            except:
                print("can not set slider value")
            pass
        elif ch == 2:
            try:
                self.CH2_verticalSlider.setMinimum(eval(self.comboBox_CH2.currentText()).minimum)
                self.CH2_verticalSlider.setMaximum(eval(self.comboBox_CH2.currentText()).maximum)
            except:
                print("can not set slider value")
            pass
         
    def Slot_Slider(self, ch):
        if ch == 1:
            self.ch1_trigvalue_label.setText(str(self.CH1_verticalSlider.value()) + eval(self.comboBox_CH1.currentText()).unit)
            pass
        elif ch == 2:
            self.ch2_trigvalue_label.setText(str(self.CH2_verticalSlider.value()) + eval(self.comboBox_CH2.currentText()).unit)
            pass
        
    def Slot_Btn_Start(self):
        if self.Btn_Start.text() == "Start":
            if not self.ch1_checkbox.isChecked() and not self.ch2_checkbox.isChecked():
                self.Msg_label.setText('Please select at least one sample channel!')
                return
            self.TimeStopFlag = 0
            self.Btn_Start.setText("Stop")
            self.Msg_label.setText('')
#             t = np.arange(0.0, 3.0, 0.01)
            self.t = np.linspace(0.,10.,self.points)
            self.ax1f1.clear()
#             if self.ch1_checkbox.isChecked():
#                 self.y = np.sin(2 * np.pi *self.t)+2
#                 self.ax1f1.plot(self.t,self.y)

            self.tim =  QTimer(self)
            self.tim.timeout.connect(self.refresh_plot)
            self.tim.start(100)
            
        elif self.Btn_Start.text() == "Stop":
            self.TimeStopFlag = 1
            self.Btn_Start.setText("Start")
         
    def refresh_plot(self):
        if self.TimeStopFlag == 1:
            self.tim.stop()
            return
        self.ttt += 0.05
        self.ax1f1.clear()
        if self.ch1_checkbox.isChecked():
            tmp_val = (eval(self.comboBox_CH1.currentText()).initial_value - eval(self.comboBox_CH1.currentText()).offset) * eval(self.comboBox_CH1.currentText()).factor
            CH1YArray.append(tmp_val)
            self.y1 = CH1YArray
            if len(CH1YArray) < self.points:
                pass
            else:
                CH1YArray.pop(0)
                if self.CH1_Trig_checkBox.isChecked():
                    #TODO: change to rise/fall edge trigger
                    if self.y1[50] == self.CH1_verticalSlider.value():
                        self.TimeStopFlag = 1
                        self.Btn_Start.setText("Start")
                        self.Msg_label.setText("Trig source:{}, Trig Value:{}, Trig Point:5".format(self.comboBox_CH1.currentText(), self.CH1_verticalSlider.value()))
                        self.TrigSig.emit()
            self.ax1f1.plot(self.t[:len(CH1YArray)],self.y1)
        '''            
        if self.ch2_checkbox.isChecked():
            CH2YArray.append(np.random.randint(-50,50))
            self.y2 = CH2YArray
            if len(CH2YArray) < self.points:
                pass
            else:
                CH2YArray.pop(0)
                if self.CH2_Trig_checkBox.isChecked():
                    if self.y2[50] == self.CH2_verticalSlider.value():
                        self.TimeStopFlag = 1
                        self.Btn_Start.setText("Start")
                        self.Msg_label.setText("Trig source:{}, Trig Value:{}, Trig Point:5".format(self.comboBox_CH2.currentText(), self.CH2_verticalSlider.value()))
                        self.TrigSig.emit()
            self.ax1f1.plot(self.t[:len(CH2YArray)],self.y2)
#             self.ax1f1.plot(self.t[:len(CH2YArray)],self.y2,'.',c='r')
        '''
                    
        if self.ch2_checkbox.isChecked():
            tmp_val = (eval(self.comboBox_CH2.currentText()).initial_value - eval(self.comboBox_CH2.currentText()).offset) * eval(self.comboBox_CH2.currentText()).factor
            CH2YArray.append(tmp_val)
            self.y2 = CH2YArray
            if len(CH2YArray) < self.points:
                pass
            else:
                CH2YArray.pop(0)
                if self.CH2_Trig_checkBox.isChecked():
                    #TODO: change to rise/fall edge trigger
                    if self.y2[50] == self.CH2_verticalSlider.value():
                        self.TimeStopFlag = 1
                        self.Btn_Start.setText("Start")
                        self.Msg_label.setText("Trig source:{}, Trig Value:{}, Trig Point:5".format(self.comboBox_CH2.currentText(), self.CH2_verticalSlider.value()))
                        self.TrigSig.emit()
            self.ax1f1.plot(self.t[:len(CH2YArray)],self.y2)
            
            
        self.canvas.draw()

            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Scope_Window()
    window.show()
    sys.exit(app.exec_())