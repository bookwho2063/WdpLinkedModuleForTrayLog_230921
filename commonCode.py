# -*- coding: utf-8 -*-
#!/usr/bin/python
import time
import winreg as reg
import requests, re
import hashlib
import json
import traceback
from datetime import datetime
import common_crypt_leedm
import logging
from logging.handlers import RotatingFileHandler

# 로그관련 글로벌 환경설정
# logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s : %(name)s : %(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
# LOG_MAX_SIZE = 1024*1024*10
# LOG_FILE_CNT = 10
# LOG_LEVEL = logging.INFO

class CustomLogger:
    """
    공통 파일로거 클래스
    """
    def __init__(self, log_file_path, log_level=logging.DEBUG, max_log_size=1024*1024, backup_count=5):
        self.log_file_path = log_file_path
        self.log_level = log_level
        self.max_log_size = max_log_size
        self.backup_count = backup_count

        # Create a console handler
        # console_handler = logging.StreamHandler()
        # console_handler.setFormatter(formatter)
        # self.logger.addHandler(console_handler)

        # Create a rotating file handler
        # file_handler = RotatingFileHandler(log_file_path, maxBytes=max_log_size, backupCount=backup_count)
        # file_handler.setFormatter(formatter)
        # self.logger.addHandler(file_handler)

    def set_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.log_level)
        self.check_logger()  # 로거 중복 방지

        # Create a formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Create TimedRotatingFileHandler
        time_handler = logging.handlers.TimedRotatingFileHandler(filename=self.log_file_path + '_day_', when='midnight', interval=1, backupCount=30, encoding='utf-8')
        time_handler.setFormatter(formatter)
        self.logger.addHandler(time_handler)
        # return self.logger

    def check_logger(self):
        if len(self.logger.handlers) > 0:
            return self.logger

    def log_info(self, message):
        self.logger.info(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_error(self, message):
        self.logger.error(message)

    def log_debug(self, message):
        self.logger.debug(message)
class commonLog:
    """
    공통 API LOG 발송 클래스
    common_log = commonCode.commonLog(userInfoDict['pharmNo'], userInfoDict['saupNo'], userInfoDict['PharmacyIdx'])
    common_log = commonCode.commonLog('', '', '')
    common_log.send_api_log("SUC-001", "샘플발송테스트")
    """
    def __init__(self, organ_number, biz_number, pharmacy_idx):
        self.organ_number = organ_number if organ_number != '' else ''
        self.biz_number = biz_number if biz_number != '' else ''
        self.pharmacy_idx = pharmacy_idx if pharmacy_idx != '' else ''

    def send_api_log(self, err_code, err_msg):
        """
        TODO 230822 API를 이용하여 로그를 DRxS로 발송한다
        :param err_code:
        :param err_msg:
        :return: 로그발송결과 True/False
        """
        try:
            now = datetime.now()

            # IP 조회
            req = requests.get("http://ipconfig.kr")
            print("(module-status) 외부 IP: ", re.search(r'IP Address : (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', req.text)[1])
            my_ip = re.search(r'IP Address : (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', req.text)[1]

            json_header = dict()
            pharm_info_dict = dict()  # 로그정보 dict
            pharm_info_dict['organ-number'] = self.organ_number
            pharm_info_dict['biz-number'] = self.biz_number
            pharm_info_dict['pharmacy_idx'] = self.pharmacy_idx
            pharm_info_dict['local_ip'] = my_ip if my_ip != '' else ''
            pharm_info_dict['error_code'] = err_code
            pharm_info_dict['error_message'] = err_msg

            # pharm_info_dict 암호화 후 입력
            print("## (send_api_log) 오류전송 최종 평문 :: {}".format(pharm_info_dict))
            json_header['drxs'] = commonCode().proc_pip_encrypt(json.dumps(pharm_info_dict))
            print("## (send_api_log) 오류전송 최종 암호문 :: {}".format(json_header))
            # 최종전달데이터 json 설정
            send_data_json = json.dumps(json_header)

            # API 전송정보
            status_data_api = "http://log.drxsolution.co.kr"
            post_headers = {'Content-Type': 'application/json', 'charset': 'utf-8', 'X-API-TYPE': 'setLinkedModuleError'}
            response_api = requests.post(status_data_api, data=send_data_json, headers=post_headers)

            print("## (send_api_log) response_api :: {}".format(response_api))
            if response_api.status_code != 200:  # API 전송 에러 오류처리
                print("## (send_api_log) 조제내역연계모듈 stauts 데이터 정보 전달 API 오류")
                return False
        except BaseException as e:
            print("## (send_api_log) 조제내역연계모듈 오류 데이터 정보 전달 실패")
            print("## (send_api_log) ERROR :: {}".format(e))
            return False
        else:
            print("## (send_api_log) 조제내역연계모듈 오류 데이터 정보 전달 성공")
            return True

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

    # def create_logger(self, sourcePath, sourceName):
    #     """
    #     로거를 생성하여 리턴합니다.
    #     :param sourcePath: 로그를 찍을 대상 파일의 경로
    #     :param sourceName: 로그파일명
    #     :return: 로거객체
    #     """
    #     try:
    #         # logger = logging.getLogger("")    # root logger 생성
    #         logfile_H = logging.handlers.RotatingFileHandler("./logs/log_test.log", maxBytes=LOG_MAX_SIZE, backupCount=LOG_FILE_CNT)
    #         # formatter = logging.Formatter('[%(asctime)s|%(levelname)s|%(funcName)s|%(lineno)d] %(message)s')
    #         formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    #         logfile_H.setFormatter(formatter)
    #         logger.addHandler(logfile_H)
    #         logger.setLevel(LOG_LEVEL)
    #
    #         logger.info("##### NEW info")
    #         logger.debug("##### NEW debug")
    #         logger.warning("##### NEW warning")
    #         logger.error("##### NEW error")
    #         logger.critical("##### NEW critical")
    #     except Exception as err:
    #         logger.error(err)
    #
    #     # return logging.getLogger(sourcePath + '/' + sourceName)
    #     return logger

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

    def proc_pip_encrypt(self, plain_json_text):
        """
        내손안의약국으로 전달할 json 데이터 str을 내부 암호화 후 리턴한다.
        :param plain_json_text: json 구조의 암호화 대상 데이터
        EX) {"result": "SUCCESS", "res_data": "", "err_code": ""}
        :return:
        """
        try:
            print('##### 자체 암호화 평문 ::', plain_json_text)
            milliseconds = str(int(time.time() * 1000))
            # prefix = hashlib.shake_128(milliseconds.encode()).digest(16)
            prefix = hashlib.md5(milliseconds.encode()).digest()
            aseEncryptedBytes = common_crypt_leedm.AESCipher256().encrypt(prefix + plain_json_text.encode())
            customEncryptedText = common_crypt_leedm.CustomCipher().encryptBytes(aseEncryptedBytes)
            print('##### 자체 암호화 결과 ::', customEncryptedText)
        except Exception as e:
            print('##### (proc_pip_encrypt) Error : ', e)
            return 'ERROR_PIP_ENCRYPT'
        else:
            return customEncryptedText

    def proc_pip_decrypt(self, enc_datas):
        """
        내손안의약국에서 전달받은 json 데이터를 내부 복호화하여 리턴한다.
        :param enc_datas:
        :return: 복호화 결과 str
        """
        try:
            milliseconds = str(int(time.time() * 1000))
            prefix = hashlib.md5(milliseconds.encode()).digest()

            print("##### 복호화 대상 데이터 :: ", enc_datas)

            customDecryptedBytes = common_crypt_leedm.CustomCipher().decrypt(enc_datas)
            print("##### 자체 복호화 결과 :: ", customDecryptedBytes, len(customDecryptedBytes))

            aseDecryptedBytes = common_crypt_leedm.AESCipher256().decrypt(customDecryptedBytes)
            dec_data = aseDecryptedBytes[len(prefix):].decode()
            print('##### 최종 복호화 결과:', dec_data)
            print('##### 최종 복호화 결과 type :', type(dec_data))
        except Exception as e:
            print('##### (proc_pip_decrypt) Error : ', e)
            print(traceback.format_exc())
            return 'ERROR_PIP_DECRYPT'
        else:
            return dec_data

    def send_api_log(self, organ_number, biz_number, pharmacy_idx, err_code, err_msg):
        """
        TODO 230822 API를 이용하여 로그를 DRxS로 발송한다
        :param organ_number: 요양기관기호
        :param biz_number: 사업자번호
        :param pharmacy_idx: 약국회원IDX
        :param err_code: 에러코드 (에러내용은 별도로 함수내에서 작성)
        :return: API 전송 완료 여부 True False
        """
        try:
            now = datetime.now()

            # IP 조회
            req = requests.get("http://ipconfig.kr")
            print("(module-status) 외부 IP: ", re.search(r'IP Address : (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', req.text)[1])
            my_ip = re.search(r'IP Address : (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', req.text)[1]

            json_header = dict()
            pharm_info_dict = dict()  # 로그정보 dict
            pharm_info_dict['organ-number'] = organ_number
            pharm_info_dict['biz-number'] = biz_number
            pharm_info_dict['pharmacy_idx'] = pharmacy_idx
            pharm_info_dict['local_ip'] = my_ip if my_ip != '' else ''
            pharm_info_dict['error_code'] = err_code
            pharm_info_dict['error_message'] = err_msg

            # pharm_info_dict 암호화 후 입력
            json_header['drxs'] = self.proc_pip_encrypt(json.dumps(pharm_info_dict))

            print("## 오류전송 최종 암호문 :: {}".format(json_header))
            # 최종전달데이터 json 설정
            send_data_json = json.dumps(json_header)

            # API 전송정보
            status_data_api = "http://log.drxsolution.co.kr"
            post_headers = {'Content-Type': 'application/json', 'charset': 'utf-8', 'X-API-TYPE': 'setLinkedModuleError'}
            response_api = requests.post(status_data_api, data=send_data_json, headers=post_headers, timeout=5)

            print("(module-status) response_api :: {}".format(response_api))
            if response_api.status_code != 200:  # API 전송 에러 오류처리
                print("## (module-status) 조제내역연계모듈 stauts 데이터 정보 전달 API 오류")
                return False
        except requests.Timeout:
            logger.log_error("(send_api_log) requests.Timeout")
        except BaseException as e:
            print("## (module-status) 조제내역연계모듈 오류 데이터 정보 전달 실패")
            print("## (module-status) ERROR :: {}".format(e))
            return False
        else:
            print("## (module-status) 조제내역연계모듈 오류 데이터 정보 전달 성공")
            return True


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

    def packageJsonSameUserInfo(self, sameuserList, pharmacyInfo):
        """
        동명이인 회원정보를 json 패키징 처리한다.
        :param sameuserList:
        :param pharmacyInfo:
        :return:
        """
        try:
            jsonStr = dict()
            jsonStr['PHARMACY_IDX'] = pharmacyInfo['PharmacyIdx']
            jsonStr['MEMBER_IDX'] = sameuserList[0]['UserId']
            jsonStr['USER_NAME'] = sameuserList[0]['UserName']
            jsonStr['MOBILE'] = sameuserList[0]['Mobile']
            jsonStr['BIRTH'] = sameuserList[0]['birth']
            jsonStr['SEX'] = sameuserList[0]['Sex']
            jsonStr['SW_TYPE'] = 'WDP'
            jsonStr['DATA_COUNT'] = str(len(sameuserList))

            sameInfoList = []
            for sameInfo in sameuserList:
                infoDict = dict()
                infoDict['CusNo'] = sameInfo['CusNo']
                infoDict['FamNo'] = sameInfo['FamNo']
                infoDict['CusNm'] = sameInfo['CusNm']
                infoDict['CusJmno'] = sameInfo['CusJmno']
                infoDict['RealBirth'] = sameInfo['RealBirth']
                infoDict['Sex'] = sameInfo['Sex']
                infoDict['CertiNo'] = sameInfo['CertiNo']
                sameInfoList.append(infoDict)
            jsonStr['Items'] = sameInfoList
        except Exception as e:
            print("(packageJsonSameUserInfo) error :: ", e)
            return ''
        else:
            return json.dumps(jsonStr)

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
        jsonStr['OtherUserId'] = userInfo['OtherUserId']

        prescriptionList = []       # 처방전 정보가 들어갈 리스트

        for index, row in dataFrames.iterrows():
            """
            처방전 데이터 갯수 만큼 dict 추가하여 리스트에 적재
            """
            prescriptionDict = dict()
            prescriptionDict['PrescriptionCd'] = row['PrescriptionCd']
            prescriptionDict['QrcodeIdx'] = row['QrcodeIdx']
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
            prescriptionDict['HospitalNm'] = row['HospitalNm']
            prescriptionDict['HospitalTel'] = row['HospitalTel']
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
        jsonStr['OtherUserId'] = userInfo['OtherUserId']

        prescriptionList = []  # 처방전 정보가 들어갈 리스트
        for index, row in dataFrames.iterrows():
            """
            처방전별 가격정보 데이터 갯수 만큼 dict 추가하여 리스트에 적재
            """
            prescriptionDict = dict()
            prescriptionDict['PrescriptionCd'] = row['PrescriptionCd']      # 220413 추가 (청구정보매핑을 위해 코드추가)
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
        jsonStr['OtherUserId'] = userInfo['OtherUserId']

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
            prescriptionDict['ItemName'] = row['ItemName']
            prescriptionDict['EdiCd'] = row['EdiCd']

            prescriptionList.append(prescriptionDict)

        print("##### prescriptionList 약정보 :: ", prescriptionList)
        jsonStr['Items'] = prescriptionList
        return json.dumps(jsonStr)

    def package_pharmacy_used_drugs_to_dict(self, dataFrames, userInfo):
        """
        약국회원의 자주쓰는 약정보 dict 패키징
        :param dataFrames: 조제약 그룹핑 코드정보
        :param userInfo: 회원정보
        :return: json str
        """

        try:
            # json Header 정보 생성
            jsonStr = dict()
            jsonStr['PHARMACY_IDX'] = userInfo['PharmacyIdx']
            jsonStr['TRANS_DATE'] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

            prescriptionList = []  # 약정보가 들어갈 리스트
            for index, row in dataFrames.iterrows():
                prescriptionDict = dict()
                prescriptionDict['DRUG_CODE'] = row['ItemCd']
                # prescriptionDict['DRUG_NAME'] = row['ItemCd']
                prescriptionList.append(prescriptionDict)

            jsonStr['ITEMS'] = prescriptionList
        except BaseException as e:
            return False
        else:
            return json.dumps(jsonStr)

    def encodeStr(self):
        """
        INI 의 정보를 인코딩하여 리턴한다.
        :return:
        """
        try:
            pass
        except Exception as e:
            print("##### (createEncrtpyKey) error :: ", e)
        else:
            pass

    def decodeStr(self, info, cKey):
        """
        INI 의 정보를 디코딩 하여 리턴한다.
        :param info: 디코딩할 문자열
        :param cKey: 디코딩 암호화 키 정보
        :return:
        """
        try:
            pass
        except Exception as e:
            print("##### (decodeIniInfo) error :: ", e)
        else:
            pass

# def sample_job():
#     print("잡 실행")
#
if __name__ == '__main__':
    logger = CustomLogger('C:\\DrxSolution_WDP\\resources\\DrxSolution_WDP.log')

    for i in range(0, 500000):
        logger.log_info("INFO LOG")
        logger.log_debug("DEBUG LOG")
        logger.log_error("ERROR LOG")
        logger.log_warning("WARNING LOG")
#
#     # 에러로그 테스트 코드
#     try:
#         print('오류 전')
#         0 / 0
#         print('오류 후')
#     except Exception as ex:
#         print('except 로 들어옴')
#         # 에러내용
#         err_msg = traceback.format_exc()
#         # 에러 API 전송 함수
#         commonCode().send_api_log(organ_number='11111111', biz_number='2223344444', pharmacy_idx='9999', err_code='ERR_DB_001', err_msg=err_msg)
#         print(err_msg)


#     print('##### commonCode')
#
#     sched_test = BackgroundScheduler()
#     sched_test.add_job(sample_job, 'interval', seconds=3, id='sample_job_1')
#     sched_test.start()
#
#     count = 0
#     while True:
#         print('running/./')
#         time.sleep(1)
#
#     sched_test.remove_job('sample_job_1')

    # commCode = commonCode()
    # key = commCode.createEncrtpyKey()
    # keys, html = commCode.callApi("https://72064269-76a7-4d86-b7d9-913ed54e8829.mock.pstmn.io/authCheck?PharmNm=%EA%B0%95%EC%A7%84%EC%95%BD%EA%B5%AD&PharmNo=00011110&SaupNo=3333333333&PharmType=WP")
    # print('keys :: ', keys)
    # print('html :: ', html)

# str = '안녕하세요 박준욱 입니다 SHA256 암호화 테스트 입니다.특수문자\n !&*#(@)(%(@&*#!(*!)#*&!(#&$%!*&#$\n숫자19823791865917862'
# sha256Str = hashlib.sha256(str.encode())
#
# print('## str :: ', str)
# print('## sha256 :: ', sha256Str.hexdigest())