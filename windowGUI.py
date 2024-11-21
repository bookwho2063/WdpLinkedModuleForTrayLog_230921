# -*- coding: utf-8 -*-
#!/usr/bin/python

import tkinter as tkinter
from tkinter import *
import queue
import os, sys
from datetime import datetime

import time
import main
import readIniFile as readIni
import windowMsgCommon as commonMsg
import webbrowser

from pystray import MenuItem as item
import pystray
from pystray import MenuItem
from PIL import Image


# DRxS.ini 파일 정보 추출
iniMng = readIni.Read_Ini(iniPath='C:\\DrxSolution_WDP\\resources\\drxsolution.ini')
iniDrxsDict = iniMng.returnIniDict('DRXS')
iniDatabaseDict = iniMng.returnIniDict('DATABASE')

class GUI:
    """
    연계모듈 GUI Class
    """
    def __init__(self):
        self.tk = tkinter.Tk()
        self.lineCount = 0
        self.cycle_count = 0
        self.tk.title("내손안의약국-처방전연계모듈-v2.0")
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
        self.btnStart = Button(self.tk, width=10, height=5, padx=20, text="실 행", repeatdelay=1000, command=lambda : self.btnSwitch('Start'))
        self.btnStop = Button(self.tk, width=10, height=5, padx=20, text="중 지", repeatdelay=1000, command=lambda : self.btnSwitch('Stop'))
        self.btnHelp = Button(self.tk, width=10, height=5, padx=20, text="원격지원", repeatdelay=1000, command=self.btnHelp)
        self.btnExit = Button(self.tk, width=10, height=5, padx=20, text="종 료", repeatdelay=1000, command=self.btnExit)
        self.btnStart.place(x=10, y=285)
        self.btnStop.place(x=170, y=285)
        self.btnHelp.place(x=330, y=285)
        self.btnExit.place(x=490, y=285)
        self.processFlag = True         # 실행 종료 플래그

    def connect_helpu(self):
        """
        헬프유 원격시스템에 연결한다.
        :return:
        """
        try:
            print("##### 내손안의약국 원격 시스템 브라우저를 연결합니다.")
            url = "http://helpu.kr/drxsolution/"
            webbrowser.open(url)
        except Exception as e:
            print("##### (btnHelp) error :: ", e)

    def module_exit(self):
        """
        연계모듈을 종료한다.
        :return:
        """
        print("트레이 및 UI 종료합니다.")
        self.tk.after_cancel(self.autoStarter)
        self.tray_icon.stop()
        self.tk.quit()
        os._exit(0)

    def tkRun(self):
        """
        GUI mainloop start
        :return:
        """
        # 트레이 생성
        # 트레이 메뉴 및 아이콘정보
        self.tray_ico_image = Image.open("C:\\DrxSolution_WDP\\img\\image_16_48.ico")
        self.tray_menu = (MenuItem('원격서비스요청', self.connect_helpu), MenuItem('프로그램종료', self.module_exit))
        self.tray_icon = pystray.Icon("내손안의약국", self.tray_ico_image, "내손안의약국-조제내역연계모듈", self.tray_menu)
        self.tray_icon.run_detached()        # 기존 run() 에서는 tkinter의 mainloop()와 thread 충돌하므로, run_detached()를 사용

        self.tk.iconbitmap('C:\\DrxSolution_WDP\\ico\\image_48.ico')
        self.tk.withdraw()      # UI를 hide 처리한다.
        self.autoStarter = self.tk.after(3000, self.btnStartClick)  # 3초 뒤 자동시작되도록 after 처리

        self.tk.protocol('WM_DELETE_WINDOW', self.hide_window)      # 종료버튼 클릭 시 트레이 실행
        # self.tk.protocol('WM_DELETE_WINDOW', self.closeEvent)   # 닫기 클릭 시 프로그램 종료
        self.tk.mainloop()

    # def show_window(self, icon, item):
    #     """
    #     트레이 윈도루를 활성화한다.
    #     :param icon:
    #     :param item:
    #     :return:
    #     """
    #     print("show_window call")
    #     icon.stop()             # 트레이 아이콘 프로세스 중지
    #     self.tk.deiconify()     # 창 활성화


    # def hide_window(self):
    #     """
    #     트레이로 작업창을 숨긴다.
    #     :return:
    #     """
    #     print("hide_window call")
    #     self.tk.withdraw()
    #     image = Image.open('./ico/image_16_48.ico')
    #     menu = (item('종료', self.quit_window), item('열기', self.show_window))
    #     icon = pystray.Icon("name", image, "내손안의약국-처방전연계모듈", menu)
    #     icon.run()
    #
    # def quit_window(self):
    #     """
    #     윈도우를 종료한다.
    #     :return:
    #     """
    #     print("quit_window call")
    #     sys.exit()


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

    def btnExit(self):
        """
        프로세스 종료 버튼 호출
        :return:
        """
        try:
            print("##### 프로세스 종료 버튼 클릭")
            self.tk.deiconify()
            self.tk.lift()
            self.closeEvent()
        except Exception as e:
            print("##### (btnExit) error :: ", e)

    def btnHelp(self):
        """
        원격지원페이지 호출
        :return:
        """
        try:
            print("##### 내손안의약국 원격 시스템 브라우저를 연결합니다.")
            url = "http://helpu.kr/drxsolution/"
            webbrowser.open(url)
        except Exception as e:
            print("##### (btnHelp) error :: ", e)

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
            commonMsg.alertMessage('내손안의약국', '프로세스 수행중 오류가 발생하였습니다.\n실행을 중지합니다.')
            self.processFlag = False
            self.btnStartClick()
            print("##### btnSwitch Exception :: ", e)

    def btnStartClick(self):
        """
        실행 버튼 클릭
        :return: 
        """
        # try:
        #     # (연계모듈실행전 사전처리 프로세스) 처방전 미처리 접수 건 정리 및 영업 외 시간 사용자 수령완료 처리건 API 요청 및 업데이트 처리
        #     common = commonCode.commonCode()
        #     regValue, regType = common.read_regist("SERVER")
        #
        #     print("##### (사전처리프로세스) 로컬DB연동 테스트를 수행합니다. :: ", iniDrxsDict)
        #
        #     # DB 연동 테스트
        #     dbConn = connDb.Manage_logcal_db(iniDatabaseDict['server'], iniDatabaseDict['database'], iniDatabaseDict['username'], iniDatabaseDict['password'])
        #     dbConn.conn_open()
        #     dbConnFlag = dbConn.send_sample_query()
        #
        #     if dbConnFlag == False:
        #         print('##### (사전처리프로세스) 샘플쿼리 동작 오류로 프로세스 종료')
        #     else:   # DB Connection Success
        #         pass
        #
        # except BaseException as e:
        #     print(traceback.format_exc())
        # else:
        #     # 처리완료
        #     pass
        # finally:    # 오류가 나더라도 연계모듈은 수행 처리한다.
        # 위드팜 조제내역 연계모듈 실행
        if self.processFlag == True:
            # 버튼상태 비활성화
            if self.btnStart['state'] == tkinter.NORMAL:
                self.btnStart['state'] = tkinter.DISABLED

            self.queue = queue.Queue()
            self.textInsert("위드팜 - 내손안의약국 조제내역 연계프로세스를 실행합니다.")
            self.lineCount = self.lineCount + 1
            self.cycle_count = self.lineCount + 1
            print("##({}) {} 회차 조제내역 연계를 수행합니다.".format(datetime.today().strftime("%Y-%m-%d %H:%M:%S"), str(self.cycle_count)))

            main.run_module(self)  # 연계 프로세스 수행

            # 연계 프로세스 수행 뒤 프로세스 재수행 after 메서드 실행
            self.processHandle = self.tk.after(int(iniDrxsDict['lifecycle']), self.btnStartClick)
            # self.processHandle = self.tk.after(10000, lambda : self.btnSwitch('Start'))
        else:
            if self.btnStart['state'] == tkinter.DISABLED:
                self.btnStart['state'] = tkinter.NORMAL

            self.textInsert("위드팜 - 내손안의약국 조제내역 연계프로세스를 중지합니다.")
            # self.tk.after(5000, lambda : self.tk.destroy())
            # self.processFlag = False

            if 'self.processHandle' in locals():
                if str(type(self.processHandle)) == "<class 'str'>":
                    self.tk.after_cancel(self.processHandle)
            else:
                self.processFlag = False
            # self.tk.after_cancel(lambda : self.btnSwitch('Stop'))
            # self.processFlag = False

    def closeEvent(self):
        """
        모듈의 '닫기'버튼 클릭시 이벤트 처리
        내부 이벤트 리스너
        :param event:
        :return:
        """
        try:
            ret_msg = tkinter.messagebox.askquestion("내손안의약국-처방전연계모듈", "처방전연계모듈을 종료하시겠습니까?\n종료 시 재실행전까지 처방전이 연계되지않습니다.", icon='warning')
            if ret_msg == 'yes':
                self.tk.destroy()
                exit()
        except BaseException as e:
            # self.mainProc.apiSetProcessTransError(errorType='ERROR', errorMsg='(closeEvent) ' + str(e))
            print("##### 닫기 버튼 오류 :: ", e)

    def btnEndClick(self):
        """
        프로세스 종료 버튼 클릭
        :return: 
        """
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

    def quit_window(self):
        print("##### quit_window")
        self.icon.stop()
        self.tk.deiconify()
        self.tk.lift()
        self.closeEvent()
        sys.exit()

    def show_window(self):
        print("##### show_window")
        self.icon.stop()
        self.tk.deiconify()
        self.tk.lift()
        # self.tk.after(1, self.tk.deiconify())

    def hide_window(self):
        self.tk.withdraw()

        # self.thread = threading.Thread(daemon=True, target=self.run_pystray)
        # self.thread.start()
        # self.thread.join()

        self.tk.iconify()

        # TODO 221128 pystray를 사용하여 트레이 아이콘 화 했을 경우 메인스레드가 tk에서 pystray로 변경되어 tk의 after가 실행되지않아 모듈연계가 진행되지않는다.
        # TODO 221128 pystray를사용하지않고 tk의 iconify를 통해 닫기버튼 클릭시 최소화 처리만 되도록 하고, 별도로 프로세스 종료 버튼을 화면내에 존재하도록하자

        # self.icon_image = Image.open(os.getcwd() + os.path.sep + "ico\\image_16_48.ico")
        # self.icon_menu = (item('연계모듈보기', self.show_window), item('연계모듈종료', self.quit_window))
        # self.icon = pystray.Icon('내손안의약국', self.icon_image, '내손안의약국-처방전연계모듈', self.icon_menu)
        # self.icon.run()


    def run_pystray(self):
        self.icon_image = Image.open("C:\\DrxSolution_WDP\\ico\\image_16_48.ico")
        self.icon_menu = (item('연계모듈보기', self.show_window), item('연계모듈종료', self.quit_window))
        self.icon = pystray.Icon('내손안의약국', self.icon_image, '내손안의약국-처방전연계모듈', self.icon_menu)
        self.icon.run()

