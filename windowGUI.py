# -*- coding: utf-8 -*-
#!/usr/bin/python

import tkinter as tkinter
from tkinter import *
import threading
import queue
import os
import time
import main
import readIniFile as readIni

# DRxS.ini 파일 정보 추출
iniMng = readIni.Read_Ini(iniPath='resource/DRxS.ini')
iniDrxsDict = iniMng.returnIniDict('DRXS')
iniDatabaseDict = iniMng.returnIniDict('DATABASE')

class GUI:
    """
    연계모듈 GUI Class
    """
    def __init__(self):
        self.tk = tkinter.Tk()
        self.lineCount = 0
        self.tk.title("내손안의약국-처방전연계모듈")
        self.tk.geometry("640x380")
        self.tk.resizable(False, False)
        self.frame = tkinter.Frame(self.tk)
        self.scrollbar = tkinter.Scrollbar(self.frame)
        self.textBox = tkinter.Text(self.frame, wrap=WORD, width=85, height=20)
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.textBox.pack(side=tkinter.LEFT, fill=tkinter.Y)
        self.scrollbar.config(command=self.textBox.yview)
        self.textBox.config(yscrollcommand=self.scrollbar.set, wrap=WORD)
        self.frame.pack()
        self.btnStart = Button(self.tk, width=20, height=5, padx=20, text="실 행", repeatdelay=1000, command=lambda : self.btnSwitch('Start'))
        self.btnStop = Button(self.tk, width=20, height=5, padx=20, text="중 지", repeatdelay=1000, command=lambda : self.btnSwitch('Stop'))
        #self.btnShowLog = Button(self.tk, width=20, height=5, padx=20, text="로그폴더", repeatdelay=1000, command=self.btnShowLogClick)
        self.btnStart.place(x=10, y=285)
        self.btnStop.place(x=225, y=285)
        #self.btnShowLog.place(x=440, y=285)
        self.processFlag = True         # 실행 종료 플래그

    def tkRun(self):
        """
        GUI mainloop start
        :return:
        """
        self.tk.mainloop()

    def textInsert(self, text):
        """
        텍스트 인서트 처리
        :param text:
        :return:
        """
        try:
            now = time.localtime()
            realtime = "[%04d-%02d-%02d %02d:%02d:%02d] " % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
            self.lineCount = self.lineCount + 1
            self.textBox.insert(int(self.lineCount) + 0.0, realtime+text+"\n")
        except Exception as e:
            print("##### textInsert error :: ", e)

    def btnSwitch(self, flag):
        """
        버튼 액션에 따른 프로세스 시작/중지 스위치 펑션
        :param flag: Start / Stop Switch
        :return:
        """
        try:
            if flag == 'Start':
                print("Start 들어옴")
                self.processFlag = True
            elif flag == 'Stop':
                print("Stop 들어옴")
                self.processFlag = False
                
            self.btnStartClick()
        except Exception as e:
            print("##### btnSwitch Exception :: ", e)

    def btnStartClick(self):
        """
        실행 버튼 클릭
        :return: 
        """
        # if self.processFlag != False:
        # main.ThreadTask(self.queue, self).start()       # 스레드 시작
        # m_thread = main.ThreadTask(self.queue, self)
        # m_thread.start()
        # m_thread.join()
        # TODO : (210727) INI 파일을 통해서 반복설정 시간을 가져와서 처리할 수 있도록 해야함
        if self.processFlag == True:
            # 버튼상태 비활성화
            if self.btnStart['state'] == tkinter.NORMAL:
                self.btnStart['state'] = tkinter.DISABLED

            self.queue = queue.Queue()
            self.textInsert("위드팜 - 내손안의약국 처방전 연계프로세스를 실행합니다.")
            self.lineCount = self.lineCount + 1

            main.run_module(self)  # 연계 프로세스 수행
            # self.processHandle = self.tk.after(10000, lambda : self.btnSwitch('Start'))

            self.processHandle = self.tk.after(int(iniDrxsDict['lifecycle']), self.btnStartClick)

        else:
            if self.btnStart['state'] == tkinter.DISABLED:
                self.btnStart['state'] = tkinter.NORMAL

            self.textInsert("위드팜 - 내손안의약국 처방전 연계프로세스를 중지합니다.")
            # self.tk.after(5000, lambda : self.tk.destroy())
            self.processFlag = False
            self.tk.after_cancel(self.processHandle)
            # self.tk.after_cancel(lambda : self.btnSwitch('Stop'))
            # self.processFlag = False

    def processExit(self):
        """
        프로그램 종료 펑션
        :return:
        """
        exit()

    def btnEndClick(self):
        """
        프로세스 종료 버튼 클릭
        :return: 
        """
        print("##### 프로세스종료버튼 클릭")
        self.textInsert("위드팜 - 내손안의약국 처방전 연계프로세스를 중지합니다.")
        self.processFlag = False

    def btnShowLogClick(self):
        """
        로그내역열기 버튼 클릭
        :return: 
        """
        logPath = iniDrxsDict['logpath']
        if os.path.isdir(logPath):
            os.startfile(logPath)
        else:
            os.mkdir(logPath)
