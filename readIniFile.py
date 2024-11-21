# -*- coding: utf-8 -*-
#!/usr/bin/python

import configparser
import traceback

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

    def update_ini_file(self, sectionName, key, value):
        """
        특정 섹션내 저장된 키의 값을 변경한다.
        :param sectionName: 변경할 섹션명
        :param key: 변경할 키의 이름
        :param value: 변경할 키의 값
        :return: 성공여부 True, False
        """
        try:
            print("##### update_ini_file call")

            iniConfiger = self.read_ini_file()
            fs = open(self.iniPath, "w")
            iniConfiger.set(sectionName, key, value)
            iniConfiger.write(fs)
            fs.close()
        except configparser.Error as e:
            print("##### update_ini_file error :: ", e)
            return 'error'

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

    def write_ini_file(self, section, name, value):
        """
        ini 파일의 특정세션의 특정값을 변경한다.
        :return: 성공여부 True/False
        """
        try:
            print("##### " + self.iniPath + "경로의 INI 파일을 쓰기처리합니다.")
            print("(쓰기-section) :: {}".format(section))
            print("(쓰기-name) :: {}".format(name))
            print("(쓰기-value) :: {}".format(value))

            config = configparser.ConfigParser()
            config.read(self.iniPath, encoding='utf-8')
            config.set(str(section), str(name), str(value))

            with open(self.iniPath, 'w') as config_file:
                config.write(config_file)
        except BaseException as e:
            print(traceback.format_exc())
            return False
        else:
            return True


# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     print("##### read INI File")
#
#     #iniMng = Read_Ini('resources/WithPharmErp.ini')
#     iniMng = Read_Ini('resources/DRxS.ini')
#     iniConfiger = iniMng.read_ini_file()
#     keyArr = iniMng.read_ini_section(iniConfiger, 'DRXS')
#     testIniData = iniMng.get_section_value(iniConfiger, 'DRXS', keyArr)
#
#     print('ppppppppp')
#     pp(testIniData)