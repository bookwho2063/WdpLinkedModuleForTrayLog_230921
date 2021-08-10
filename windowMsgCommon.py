import tkinter
import tkinter.messagebox

def alertMessage(msgTitle, msg):
    """
    공통 메시지를 윈도우에 출력한다.
    :param msgTitle: 메세지 제목
    :param msg: 메세지 내용
    :return:
    """
    tkinter.messagebox.showinfo(msgTitle, msg)

# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     print('window msg common loaded')
#
#     alertMessage('내손안의약국', '알림창 테스트 입니다.')
