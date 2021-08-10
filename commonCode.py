# -*- coding: utf-8 -*-
#!/usr/bin/python

import winreg as reg
import logging
import logging.handlers
import requests
import os
import hashlib
import json
import connectionDbPyodbc as connDb

# 로그관련 글로벌 환경설정
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s : %(name)s : %(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
LOG_MAX_SIZE = 1024*1024*10
LOG_FILE_CNT = 10
LOG_LEVEL = logging.INFO

class commonCode:
    """
    공통코드 클래스
    """
    def __init__(self):
        pass

    def callApi(self, url):
        """
        API 요청을 공통으로 처리한다.
        :param url:
        :return: API 호출 결과 Keys / Dict
        """
        resultJson = requests.get(url)

        jsonToDict = resultJson.json()
        dictKeys = jsonToDict.keys()

        return dictKeys, jsonToDict

    def create_logger(self, sourcePath, sourceName):
        """
        로거를 생성하여 리턴합니다.
        :param sourcePath: 로그를 찍을 대상 파일의 경로
        :param sourceName: 로그파일명
        :return: 로거객체
        """
        try:
            logger = logging.getLogger("")    # root logger 생성
            logfile_H = logging.handlers.RotatingFileHandler("./logs/log_test.log", maxBytes=LOG_MAX_SIZE, backupCount=LOG_FILE_CNT)
            # formatter = logging.Formatter('[%(asctime)s|%(levelname)s|%(funcName)s|%(lineno)d] %(message)s')
            formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            logfile_H.setFormatter(formatter)
            logger.addHandler(logfile_H)
            logger.setLevel(LOG_LEVEL)

            logger.info("##### NEW info")
            logger.debug("##### NEW debug")
            logger.warning("##### NEW warning")
            logger.error("##### NEW error")
            logger.critical("##### NEW critical")
        except Exception as err:
            logger.error(err)

        # return logging.getLogger(sourcePath + '/' + sourceName)
        return logger

    def read_regist(self, regName):
        """
        레지스트리 편집기 상의 WPharmErp 레지스트리 정보를 추출한다.
        :return:
        """
        print("##### 위드팜 레지스트리 정보를 추출합니다.")
        key = reg.HKEY_CURRENT_USER
        key_value = "Software\WPharmErp"

        open = reg.OpenKey(key, key_value, 0, reg.KEY_ALL_ACCESS)

        try:
            """
            검색 타겟 종류
            DataDte
            DataYn
            Dev
            Membership
            NimsReg
            OrderServer
            PHARMNO
            SERVER
            SYSTEMPATH
            UPDATESERVER
            UpMaster
            UPUSER
            USERID
            Version
            """
            value, type = reg.QueryValueEx(open, regName)
            print("##### (레지스트리검색)"+regName+" :: ", value, " :: type :: ", type)
            return value, type
        except FileNotFoundError:
            print('##### 레지스트리 파일을 찾을 수 없습니다.')

    def dictToJson(self, dictData):
        """
        딕셔너리 형태의 데이터를 json 형태로 변환한다.
        :param dictData:
        :return: json 데이터
        """
        try:
            result = json.dumps(dictData)
            return result
        except json.JSONDecodeError as e:
            print("##### dictToJson Error :: ", e.msg)
            return False



    def jsonToDict(self, jsonData):
        """
        json 데이터를 딕셔너리 형태로 변환한다.
        :param jsonData:
        :return: 딕셔너리데이터
        """
        try:
            result = json.loads(jsonData)
            return result
        except json.JSONDecodeError as e:
            print("##### jsonToDict Error :: ", e.msg)
            return False

    def packageJsonPrescription(self, dataFrames, userInfo):
        """
        회원별 처방전 조회 내역을 API 전송을 위한 JSON으로 패키징
        :param dataFrames: 처방전 정보
        :param userInfo: 회원정보
        :return:
        """

        # dataFrames 의 갯수가 5개가 넘어갈 경우, 5개씩 끊어서 생성한다.

        # json Header 정보 생성
        jsonStr = dict()
        jsonStr['PharmacyIdx'] = userInfo['PharmacyIdx']
        jsonStr['CusNo'] = userInfo['CusNo']
        jsonStr['UserId'] = userInfo['UserId']
        jsonStr['CusNm'] = userInfo['CusNm']
        jsonStr['RealBirth'] = userInfo['RealBirth']
        jsonStr['CusJmno'] = userInfo['CusJmno']

        prescriptionList = []       # 처방전 정보가 들어갈 리스트

        for index, row in dataFrames.iterrows():
            """
            처방전 데이터 갯수 만큼 dict 추가하여 리스트에 적재
            """
            prescriptionDict = dict()
            prescriptionDict['PrescriptionCd'] = row['PrescriptionCd']
            prescriptionDict['CusNo'] = row['CusNo']
            prescriptionDict['InsuGb'] = row['InsuGb']
            prescriptionDict['CareGb'] = row['CareGb']
            prescriptionDict['InsuEtc'] = row['InsuEtc']
            prescriptionDict['SendGb'] = row['SendGb']
            prescriptionDict['RootCusNm'] = row['RootCusNm']
            prescriptionDict['PromissNo'] = row['PromissNo']
            prescriptionDict['InsuNo'] = row['InsuNo']
            prescriptionDict['CusNm'] = row['CusNm']
            prescriptionDict['CusJmno'] = row['CusJmno']
            prescriptionDict['HospitalNo'] = row['HospitalNo']
            prescriptionDict['Doctor'] = row['Doctor']
            prescriptionDict['DoctorSeq'] = row['DoctorSeq']
            prescriptionDict['MakeDte'] = row['MakeDte']
            prescriptionDict['PregYn'] = row['PregYn']
            prescriptionDict['MakeDay'] = row['MakeDay']
            prescriptionDict['ConDay'] = row['ConDay']
            prescriptionDict['PresDte'] = row['PresDte']
            prescriptionDict['PresNo'] = row['PresNo']
            prescriptionDict['UseDay'] = row['UseDay']
            prescriptionDict['DisCd1'] = row['DisCd1']
            prescriptionDict['DisCd2'] = row['DisCd2']
            prescriptionDict['SpecialCd'] = row['SpecialCd']
            prescriptionDict['LicenseNo'] = row['LicenseNo']
            prescriptionDict['BabyYn'] = row['BabyYn']
            prescriptionDict['OverTime'] = row['OverTime']
            prescriptionDict['UserTime'] = row['UserTime']
            prescriptionDict['StateGb'] = row['StateGb']
            prescriptionDict['CareHospitalGb'] = row['CareHospitalGb']
            prescriptionDict['RDte'] = row['RDte']
            prescriptionDict['RUser'] = row['RUser']
            prescriptionDict['MDte'] = row['MDte']
            prescriptionDict['MUser'] = row['MUser']
            prescriptionDict['CDte'] = row['CDte']
            prescriptionDict['CUser'] = row['CUser']
            prescriptionDict['DelYn'] = row['DelYn']
            prescriptionDict['ErrGb'] = row['ErrGb']
            prescriptionDict['LabelYn'] = row['LabelYn']
            prescriptionDict['PrescriptionSeq'] = row['PrescriptionSeq']
            prescriptionDict['PosPayGb'] = row['PosPayGb']
            prescriptionDict['NimsGb'] = row['NimsGb']
            prescriptionDict['PowderYn'] = row['PowderYn']
            prescriptionList.append(prescriptionDict)

        jsonStr['Items'] = prescriptionList
        print("##### 처방전 전송 최종 JSON :: ", json.dumps(jsonStr))
        return json.dumps(jsonStr)


    def packageJsonPrescriptionAmt(self, dataFrames, userInfo):
        """
        회원별 처방전 가격 내역을 API 전송을 위한 JSON으로 패키징
        :param dataFrames: 처방전 정보
        :param userInfo: 회원정보
        :return:
        """
        # json Header 정보 생성
        jsonStr = dict()
        jsonStr['PharmacyIdx'] = userInfo['PharmacyIdx']
        jsonStr['CusNo'] = userInfo['CusNo']
        jsonStr['UserId'] = userInfo['UserId']
        jsonStr['CusNm'] = userInfo['CusNm']
        jsonStr['RealBirth'] = userInfo['RealBirth']
        jsonStr['TransDt'] = 'yyyymmdd'
        jsonStr['TotalCount'] = len(dataFrames)

        prescriptionList = []  # 처방전 정보가 들어갈 리스트
        for index, row in dataFrames.iterrows():
            """
            처방전별 가격정보 데이터 갯수 만큼 dict 추가하여 리스트에 적재
            """
            prescriptionDict = dict()
            prescriptionDict['tAmt1'] = row['tAmt1']
            prescriptionDict['sAmt'] = row['sAmt']
            prescriptionDict['BillAmt'] = row['BillAmt']
            prescriptionDict['SupportAmt'] = row['SupportAmt']
            prescriptionDict['tAmt2'] = row['tAmt2']
            prescriptionDict['mBillAmt'] = row['mBillAmt']
            prescriptionDict['DrugDiffAmt'] = row['DrugDiffAmt']
            prescriptionDict['TotAmt'] = row['TotAmt']
            prescriptionDict['t100Amt'] = row['t100Amt']
            prescriptionDict['mAmt'] = row['mAmt']
            prescriptionDict['t100mAmt'] = row['t100mAmt']
            prescriptionDict['s100mAmt'] = row['s100mAmt']
            prescriptionDict['Bill100mtAmt'] = row['Bill100mtAmt']
            prescriptionDict['Bill100mmAmt'] = row['Bill100mmAmt']
            prescriptionDict['Rate'] = row['Rate']
            prescriptionDict['TotalSelfAmt'] = row['TotalSelfAmt']
            prescriptionDict['mTotBAmt'] = row['mTotBAmt']
            prescriptionDict['mBillBAmt'] = row['mBillBAmt']
            prescriptionDict['TotalAmt'] = row['TotalAmt']
            prescriptionDict['BExcept'] = row['BExcept']

            prescriptionList.append(prescriptionDict)

        print("##### prescriptionList :: ", prescriptionList)
        jsonStr['Items'] = prescriptionList
        return json.dumps(jsonStr)

    def packageJsonPrescriptionDrug(self, dataFrames, userInfo):
        """
        회원별 조제약 내역을 API 전송을 위한 JSON으로 패키징
        :param dataFrames: 처방전 정보
        :param userInfo: 회원정보
        :return:
        """
        # json Header 정보 생성
        jsonStr = dict()
        jsonStr['PharmacyIdx'] = userInfo['PharmacyIdx']
        jsonStr['CusNo'] = userInfo['CusNo']
        jsonStr['UserId'] = userInfo['UserId']
        jsonStr['CusNm'] = userInfo['CusNm']
        jsonStr['RealBirth'] = userInfo['RealBirth']
        jsonStr['TransDt'] = 'yyyymmdd'
        jsonStr['TotalCount'] = len(dataFrames)

        prescriptionList = []  # 처방전 정보가 들어갈 리스트
        for index, row in dataFrames.iterrows():
            """
            처방전 별 약데이터 갯수 만큼 dict 추가하여 리스트에 적재
            """
            prescriptionDict = dict()
            prescriptionDict['PrescriptionCd'] = row['PrescriptionCd']
            prescriptionDict['Seq'] = row['Seq']
            prescriptionDict['Gb'] = row['Gb']
            prescriptionDict['ItemType'] = row['ItemType']
            prescriptionDict['ItemCd'] = row['ItemCd']
            prescriptionDict['Price'] = row['Price']
            prescriptionDict['EatDay'] = row['EatDay']
            prescriptionDict['TotDay'] = row['TotDay']
            prescriptionDict['EatOnce'] = row['EatOnce']
            prescriptionDict['TotQty'] = row['TotQty']
            prescriptionDict['Amt'] = row['Amt']
            prescriptionDict['MaxAmt'] = row['MaxAmt']
            prescriptionDict['DrugDiffAmt'] = row['DrugDiffAmt']
            prescriptionDict['MakeGb'] = row['MakeGb']
            prescriptionDict['EatGb'] = row['EatGb']
            prescriptionDict['PasYn'] = row['PasYn']
            prescriptionDict['LinkLabel'] = row['LinkLabel']
            prescriptionDict['ItemSeq'] = row['ItemSeq']
            prescriptionDict['EatComment'] = row['EatComment']

            prescriptionList.append(prescriptionDict)

        print("##### prescriptionList :: ", prescriptionList)
        jsonStr['Items'] = prescriptionList
        return json.dumps(jsonStr)

# if __name__ == '__main__':
#     print('##### commonCode')
#
#     commCode = commonCode()
#     keys, html = commCode.callApi("https://72064269-76a7-4d86-b7d9-913ed54e8829.mock.pstmn.io/authCheck?PharmNm=%EA%B0%95%EC%A7%84%EC%95%BD%EA%B5%AD&PharmNo=00011110&SaupNo=3333333333&PharmType=WP")
#     print('keys :: ', keys)
#     print('html :: ', html)
#
# str = '안녕하세요 박준욱 입니다 SHA256 암호화 테스트 입니다.특수문자\n !&*#(@)(%(@&*#!(*!)#*&!(#&$%!*&#$\n숫자19823791865917862'
# sha256Str = hashlib.sha256(str.encode())
#
# print('## str :: ', str)
# print('## sha256 :: ', sha256Str.hexdigest())