# -*- coding: utf-8 -*-
#!/usr/bin/python
import tkinter as tkinter
from tkinter import *

import schedule
import time

count = 0

class moduleGui:
    """
    모듈의 GUI 처리를 담당하는 클래스
    """
    lineCount = 0

    def __init__(self):
        pass

    def createWindow(self):
        """
        TK 윈도우 생성
        :return: tk
        """
        print("##### 윈도우 객체를 생성합니다.")
        try:
            root = Tk()
            root.title("내손안의약국-처방전연계모듈")
            root.geometry("640x380")
            root.resizable(False, False)

            frame = tkinter.Frame(root)
            scrollBar = tkinter.Scrollbar(frame)
            textArea = tkinter.Text(frame, wrap=WORD, width=85, height=20)

            scrollBar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
            textArea.pack(side=tkinter.LEFT, fill=tkinter.Y)
            frame.pack()

            scrollBar.config(command=textArea.yview)
            textArea.config(yscrollcommand=scrollBar.set, wrap=WORD)

            btnStart = Button(root, width=20, height=5, padx=20, text="실 행", repeatdelay=1000, command=lambda: self.btnClickStart(textArea, count))
            btnStop = Button(root, width=20, height=5, padx=20, text="중 지", command=lambda: self.btnClickEnd())
            btnLog = Button(root, width=20, height=5, padx=20, text="로그내역 열기", command=lambda: self.btnClickLogOpen())

            btnStart.place(x=10, y=285)
            btnStop.place(x=225, y=285)
            btnLog.place(x=440, y=285)

            return root, textArea
        except Exception as e:
            print("##### 윈도우 객체 생성중 오류가 발생하였습니다.\n", e)

    def btnClickStart(self, listbox, count):
        """
        시작버튼클릭
        :return:
        """
        print("##### GUI 시작버튼 클릭 :: ")
        print("##### lineCount :: ", count)
        listbox.insert(count + 0.0, "시작버튼이 클릭되었습니다.!!! lineCount : {}\n".format(count))

    def btnClickEnd(self):
        """
        중지버튼클릭
        :return:
        """
        print("##### 중지버튼 클릭")
        # 중지 시 스케줄러 중지

    def btnClickLogOpen(self):
        """
        로그내역열기
        :return:
        """
        print("##### 로그내역버튼 클릭")

# if __name__ == "__main__":
#     print("##### GUI TEST")
#     commGui = moduleGui()
#     root, textArea = commGui.createWindow()
#     textArea.insert(0.0, "메시지 들어갑니까????")
#     root.mainloop()     # 화면실행

