# -*- coding: utf-8 -*-
#!/usr/bin/python

import configparser
from pprint import pprint as pp

class Read_Ini:
    """
    환경설정 INI 파일 핸들링 클래스
    """
    def __init__(self, iniPath):
        self.iniPath = iniPath

    def read_ini_file(self):
        """
        환경설정 INI 파일을 읽어서 configParser 객체 리턴
        :param filePath:
        :return: configParser 객체
        """
        try:
            config = configparser.ConfigParser()
            config.read(self.iniPath, encoding='utf-8')
            sec = config.sections()
            print("##### 설정정보 INI 읽기 완료")
            return config
        except configparser.Error as e:
            print("##### 설정정보 INI 핸들링 중 오류가 발생하였습니다.")

    def read_ini_section(self, config, sectionName):
        """
        특정 섹션내 저장된 키:벨류 값 추출
        :param config:
        :param sectionName:
        :return:
        """
        try:
            keyArr = config[sectionName]
            print("##### keyArr : ", keyArr)
            return keyArr
        except configparser.Error as e:
            print("##### 설정정보 INI 키셋 추출 중 오류가 발생하였습니다.")


    def get_section_value(self, config, sectionName, keyArr):
        """
        특정 섹션 내 키의 값들을 딕셔너리형태로 변환하여 리턴
        :param config:
        :param keyArr:
        :return:
        """
        try:
            resultDict = dict()
            for key in keyArr:
                resultDict[key] = config.get(sectionName, key)

            return resultDict
        except configparser.Error as e:
            print("##### 설정정보 INI 딕셔너리 생성 중 오류가 발생하였습니다.")


    def returnIniDict(self, sectionName):
        """
        sectionName에 해당하는 섹션내 환경값을 Dict 형태로 리턴한다.
        :param sectionName:
        :return: Dict
        """
        try:
            iniConfiger = self.read_ini_file()
            keyArr = self.read_ini_section(iniConfiger, sectionName=sectionName)
            iniData = self.get_section_value(iniConfiger, sectionName, keyArr)

            return iniData
        except configparser.Error as e:
            print("##### 설정정보 INI 환경정보 딕셔너리 생성 중 오류가 발생하였습니다.")



# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     print("##### read INI File")
#
#     #iniMng = Read_Ini('resource/WithPharmErp.ini')
#     iniMng = Read_Ini('resource/DRxS.ini')
#     iniConfiger = iniMng.read_ini_file()
#     keyArr = iniMng.read_ini_section(iniConfiger, 'DRXS')
#     testIniData = iniMng.get_section_value(iniConfiger, 'DRXS', keyArr)
#
#     print('ppppppppp')
#     pp(testIniData)