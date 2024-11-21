# -*- coding: utf-8 -*-
#!/usr/bin/python
import json
import traceback

import requests
from win32com.server.exception import Exception

import winreg
import commonCode
import connectionDbPyodbc as connDb
import connectionApi as connApi
import readIniFile as readIni
import windowGUI
from threading import Timer
from datetime import datetime
import common_process
import pandas as pd

# 로그 파일 import
import common_log as logger_file

# 모듈 사용 약국정보 딕셔너리 전역변수
userInfoDict = dict()

# 최종연계회원정보리스트 전역변수
userInfoListGlobal = []

# 최초 1회 수행 완료여부 Flag (미처리 처방전 데이터 삭제 및 API 전달 / 미처리 수령완료 정보 API 요청 및 처리)
is_pre_clear_process_flag = 'N'
is_pre_visit_process_flag = 'N'

# 레지스트리를 이용하여 INI정보 업데이트
try:
    regRoot = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    regSub = winreg.OpenKey(regRoot, 'SOFTWARE\\WPharmErp')
    regServerValue, regServerType = winreg.QueryValueEx(regSub, 'SERVER')
except FileNotFoundError as e:
    print("(WPharmErp) 레지스트리정보가 존재하지않습니다.")
    regServerValue = ''
    regServerType = ''
    regSub = ''

iniMng = readIni.Read_Ini(iniPath='C:\\DrxSolution_WDP\\resources\\drxsolution.ini')
if regServerValue != '':
    if iniMng.update_ini_file("DATABASE", "SERVER", regServerValue) == 'error':
        print("##### INI 설정정보 변경에 실패하였습니다.")
        raise ConnectionError
else:
    print("(regServerValue) 정보 미존재 레지스트리 정보로 ini 업데이트 미실시")

# DRxS.ini 파일 정보 추출
iniDrxsDict = iniMng.returnIniDict('DRXS')
iniDatabaseDict = iniMng.returnIniDict('DATABASE')

# 로그 TextBox 영역 라인카운트
lineCount = 0

# 스케줄러 수행 플래그값
scheduleFlag = 'Y'

# 처방전 초기화 수행여부 Flag
global prescription_clear_flag
prescription_clear_flag = 'N'

# 조제내역 싱크매핑용 글로벌 변수 Flag
global prescription_mapping_flag
prescription_mapping_flag = 'N'



# 로거 생성 (common_log 사용하므로 주석처리함)
# logger_path = "C:\\DrxSolution_WDP\\logs"
# # logs 폴더 존재여부 확인 및 미존재시 폴더 생성
# try:
#     if not os.path.exists(logger_path):
#         os.makedirs(logger_path)
# except OSError:
#     print("logs 폴더 생성 실패 :: {}".format(traceback.format_exc()))
# logger_file_class = commonCode.CustomLogger(logger_path + '\\DrxSolution_WDP_log')
# logger_file = logger_file_class.set_logger()
logger_api = commonCode.commonCode()

# 스케줄러 생성
# glob_sched = BackgroundScheduler(timezone='Asia/Seoul')  # 기존작업외에 수행해야하므로 백그라운드 스케쥴러로 생성
# glob_sched = BackgroundScheduler()  # 기존작업외에 수행해야하므로 백그라운드 스케쥴러로 생성

global PharmNm      # 약국명
global PharmNo      # 약국요양기관번호
global SaupNo       # 약국사업자번호
global PharmIdx     # 약국회원 고유번호 IDX

def environmental_inspection_part(gui_root):
    """
    모듈 연계 환경검사 함수
    :param gui_root: GUI 정보
    :return: 환경검사 결과정보
    """
    # TODO : 레지스트리 정보 추출하여 INI파일에 적용 (완)
    common = commonCode.commonCode()
    # regValue, regType = common.read_regist("SERVER")

    gui_root.textInsert("위드팜 - 내손안의약국 처방전 연계프로세스 환경검사를 수행합니다.")
    print("##### (environmental_inspection_part) 로컬DB연동 테스트를 수행합니다. :: ", iniDrxsDict)

    # DB 연동 테스트
    dbConn = connDb.Manage_logcal_db(iniDatabaseDict['server'], iniDatabaseDict['database'], iniDatabaseDict['username'], iniDatabaseDict['password'], iniDatabaseDict['conntime'] if 'conntime' in iniDatabaseDict else 1800)
    db_conn_flag = dbConn.conn_open()

    if db_conn_flag:
        dbConnFlag = dbConn.send_sample_query()
        # logger_api.send_api_log('','','999999','SUC-100', '약국DB 연결완료')
    elif not db_conn_flag:
        return False
    else:   # DB 연결실패로 인해 alert 띄우지않고 다음 사이클시간까지 대기
        return False

    if not dbConnFlag:
        print('##### (environmental_inspection_part) 샘플쿼리 동작 오류로 프로세스 종료')
        gui_root.textInsert("ERROR :: 데이터베이스 접근 오류로 프로세스를 종료합니다.")
        logger_file.log_error("ERROR :: 데이터베이스 접근 오류로 프로세스를 종료합니다.")
        logger_api.send_api_log('', '', '999999', 'ERR-002', '약국 DB 연결 실패')
        return False

    # logger_file.log_info("약국 DB Connection 테스트 완료.")
    dbConn.conn_close()

    # 회원 여부 검증을 위하여 회원정보 추출
    gui_root.textInsert("INFO :: 약국회원정보를 추출하여 내손안의약국 회원여부를 판별합니다.")
    dbConn.conn_open()
    tempQuery = []
    tempQuery.append("SELECT")
    tempQuery.append("TOP 1")
    tempQuery.append("PharmNm")
    tempQuery.append(", PharmNo")
    tempQuery.append(", SaupNo")
    tempQuery.append(", CeoNm")
    tempQuery.append(", CeoJmno")           
    tempQuery.append("FROM dbo.InfoCompany")
    userCertificationQuery = " ".join(tempQuery)
    queryResult = dbConn.send_query(userCertificationQuery)
    dbConn.conn_close()

    # 쿼리결과 error 일 경우 리턴처리
    if type(queryResult) == bool and not queryResult:
        logger_file.log_error("(쿼리결과오류) 약국회원정보 조회 쿼리 실행 오류 (dbo.InfoCompany)")
        logger_api.send_api_log('', '', '999999', 'ERR-100', '(쿼리결과오류) 약국회원정보 조회 쿼리 실행 오류')
        return False

    print("### (약국정보조회) :: {}".format(queryResult))
    # logger_file.log_info("(위드팜-약국정보조회) 쿼리 결과 :: {}".format(queryResult))

    # TODO 231004 GET방식 API POST방식 + 암호화 전환으로인해 데이터 변환
    send_body_data = dict()
    send_body_data['PharmNo'] = str(queryResult.iloc[0][1])
    send_body_data['SaupNo'] = str(queryResult.iloc[0][2])

    # API 서버 커넥션 체크
    mngApi = connApi.api_manager()

    # 등록 약국 1차 검증 API URL
    checkUrl = iniDrxsDict['apiurl'] + '/apiServerConn_v1.drx'
    # print('##### checkUrl :: ', checkUrl)

    result_flag, result_msg = mngApi.api_conn_post(checkUrl, json.dumps(send_body_data))
    if type(result_flag) == bool and not result_flag:
        print(result_msg)
        gui_root.textInsert("WARNING :: 위드팜 - 내손안의약국 처방전 연계 회원약국이 아닙니다.")
        logger_file.log_error("(위드팜-약국정보조회) 내손안의약국 회원약국이 아닙니다.")
        # logger_api.send_api_log('', '', '999999', 'ERR-001', 'NOT PHARMACY MEMBER')
        return False

    if type(result_msg) != dict:
        logger_file.log_error("apiServerConn_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
        return False

    # if mngApi.api_conn_check(checkUrl) == "NO_USER":
    #     gui_root.textInsert("WARNING :: 위드팜 - 내손안의약국 처방전 연계 회원약국이 아닙니다.")
    #     logger_file.log_error("(위드팜-약국정보조회) 내손안의약국 회원약국이 아닙니다.")
    #     logger_api.send_api_log('', '', '999999', 'ERR-001', 'NOT PHARMACY MEMBER')
    #     return False

    # TODO 231004 GET방식 API POST방식 + 암호화 전환으로인해 데이터 변환
    send_body_data = dict()
    send_body_data['PharmNm'] = str(queryResult.iloc[0][0])
    send_body_data['PharmNo'] = str(queryResult.iloc[0][1])
    send_body_data['SaupNo'] = str(queryResult.iloc[0][2])
    send_body_data['PharmSwType'] = str(iniDrxsDict['moduletype'])

    # API를 이용하여 내손안의약국 약국회원 인증 2차검증
    certifiApiUrl = iniDrxsDict['apiurl']+'/authCheck_v1.drx'
    certifiApiKeys, certifiApiDic = mngApi.api_conn_post(certifiApiUrl, json.dumps(send_body_data))

    if type(certifiApiKeys) == bool and not certifiApiKeys:
        logger_file.log_error("(위드팜-약국정보조회) API 전송 오류 발생")
        logger_file.log_error("(위드팜-약국정보조회) ERROR :: {}".format(certifiApiDic))
        # logger_api.send_api_log('', '', '999999', 'ERR-200', 'API requests.exception :: {}'.format(certifiApiDic))

    if type(certifiApiDic) != dict:
        logger_file.log_error("authCheck_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
        return False

    print("### this certifiApiKeys :: ", certifiApiKeys)
    print("### this certifiApiDic :: ", certifiApiDic)

    splitTemp = certifiApiDic['LinkTargetDate'].split(' ')
    certifiApiDic['LinkTargetDate'] = splitTemp[0]
    del(splitTemp)      # 사용하지않는 변수 삭제
    print("##### 회원인증 결과 정보(KEY) :: ", certifiApiKeys)
    print("##### 회원인증 결과 정보(VALUE) :: ", certifiApiDic)

    # 회원약국 체크 후 결과 값 검증
    if certifiApiDic['Status'] == 'error':
        print("##### (환경검사) 회원약국이 아닙니다.")
        gui_root.textInsert("WARNING :: 위드팜 - 내손안의약국 처방전 연계 회원약국이 아닙니다.")
        logger_api.send_api_log('', '', '999999', 'ERR-001', 'NOT PHARMACY MEMBER (회원약국이아닙니다)')
        return False
    elif certifiApiDic['Status'] == 'ok':
        print("##### (환경검사) {} 약국회원 인증 완료!! ".format(queryResult.iloc[0][0]))
        gui_root.textInsert(str("내손안의약국 처방전 연계 회원 \'{}\' 약국의 접속인증을 완료하였습니다.".format(queryResult.iloc[0][0])))
        # 전역변수 약국회원정보 지정
        global PharmNm
        global PharmNo
        global SaupNo
        global PharmIdx
        PharmNm = queryResult.iloc[0][0]
        PharmNo = queryResult.iloc[0][1]
        SaupNo = queryResult.iloc[0][2]
        PharmIdx = certifiApiDic['PharmacyIdx']

        userInfoDict['pharmNm'] = queryResult.iloc[0][0]
        userInfoDict['pharmNo'] = queryResult.iloc[0][1]
        userInfoDict['saupNo'] = queryResult.iloc[0][2]
        userInfoDict['ceoNm'] = queryResult.iloc[0][3]
        userInfoDict['ceoJmNo'] = queryResult.iloc[0][4]
        userInfoDict['PharmacyIdx'] = PharmIdx
        userInfoDict['linkTargetDate'] = str(certifiApiDic['LinkTargetDate'])
        userInfoDict['pharmacySoftware'] = str(certifiApiDic['PharmacySoftware'])
        userInfoDict['pharmacyIdx'] = str(certifiApiDic['PharmacyIdx'])
        userInfoDict['CallTransDrugYn'] = str(certifiApiDic['CallTransDrugYn'])     # Y 일경우 약국의 최근조제 약정보 전송, N이면 제외

        # print("##### 회원 인증 후 userInfoDict :: ", userInfoDict)

        # TASK : 약국의 자주쓰는 약정보 조회 및 API 전송 (3개월 이전 데이터 중에서 검색)
        if str(userInfoDict['CallTransDrugYn']) == 'Y':     # 회원인증 API에서 약정보 조회 요청이 Y 일 경우에만 3개월 전 약정보를 조회하여 전달한다.
            dbConn.conn_open()
            tempQuery = []
            tempQuery.append("SELECT")
            tempQuery.append(" PD.ItemCd")
            tempQuery.append(" FROM WithpharmErp.dbo.Prescription AS PR")
            tempQuery.append(" INNER JOIN WithpharmErp.dbo.PrescriptionDrug AS PD")
            tempQuery.append(" ON PD.PrescriptionCd = PR.PrescriptionCd")
            # 최근 3개월 이전부터 오늘까지의 조제완료된 약정보를 조회하여 API 발송처리한다.
            tempQuery.append(" WHERE CONVERT(VARCHAR, PR.RDte, 112) BETWEEN CONVERT(VARCHAR, DATEADD(MONTH, -3, GETDATE()), 112) AND CONVERT(VARCHAR, GETDATE(), 112)")
            tempQuery.append(" AND PR.StateGb <> '1'")
            tempQuery.append(" GROUP BY PD.ItemCd")
            pharmacy_trans_drugs_query = " ".join(tempQuery)
            pharmacy_trans_drugs_query_result = dbConn.send_query(pharmacy_trans_drugs_query)
            dbConn.conn_close()

            # print("##### 약정보 조회 결과 :: ")
            # print(pharmacy_trans_drugs_query_result)

            if type(pharmacy_trans_drugs_query_result) == bool and not pharmacy_trans_drugs_query_result:
                return False

            # DF to json
            drugs_info_json = commonCode.commonCode().package_pharmacy_used_drugs_to_dict(pharmacy_trans_drugs_query_result, userInfoDict)
            # print("##### 약정보 조회 결과 to json :: ", drugs_info_json)
            if not drugs_info_json:
                logger_file.log_info("약국 자주쓰는 약정보 변환 중 오류가 발생하였습니다 (drugs_info_json)")
                logger_api.send_api_log(userInfoDict['pharmNo'], userInfoDict['saupNo'], userInfoDict['pharmacyIdx'], 'ERR-300', '(자주쓰는약정보 API전달)DataFrame to JSON ERROR')
                return False

            # 약 정보 API 전달
            mngApi = connApi.api_manager()

            checkUrl = iniDrxsDict['apiurl'] + '/transPharmacyDrugs_v1.drx'  # 검증완료 동명이인 요청 API URL
            apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrl, drugs_info_json)  # POST API 로 전송

            if type(apiResultDatas) != dict:
                logger_file.log_error("transPharmacyDrugs_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
                return False

            if apiResultDatas['Status'] != 'SUCCESS':
                print("##### 약정보 전달 오류 :: ", apiResultDatas['Status'])
                logger_api.send_api_log(userInfoDict['pharmNo'], userInfoDict['saupNo'], userInfoDict['pharmacyIdx'],'ERR-201', '(자주쓰는약정보 API전달)API SEND ERROR (STATUS :: {})'.format(apiResultDatas['Status']))
                return False
            else:
                print("##### 약정보 전달 결과 :: ", apiResultDatas)

        return True

def send_confirm_samename_user_info():
    """
    내손안의약국에서 검증완료 처리된 동명이인 정보 요청
    DATE : 22.04.25
    :return: 전송완료시 True, 실패시 False
    """
    try:
        mngApi = connApi.api_manager()

        datas = dict()
        datas['PHARMACY_IDX'] = userInfoDict['PharmacyIdx']
        params = json.dumps(datas)

        checkUrl = iniDrxsDict['apiurl'] + '/getMemberPharmacySameNameChoice_v1.drx'  # 검증완료 동명이인 요청 API URL
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrl, params)  # POST API 로 전송

        if type(apiResultDatas) != dict:
            logger_file.log_error("getMemberPharmacySameNameChoice_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
            return False

    except Exception as e:
        print("##### (send_confirm_samename_user_info) error :: ", e)
        return False
    else:
        if apiResultDatas['Status'] == 'ok':
            return apiResultDatas
        else:
            return False

def send_favority_user_info():
    """
    단골회원 중 연계회원(1,2차 회원)정보를 내손안의약국으로 API 전송한다.
    DATE : 22.04.25
    :return: 전송완료시 True, 실패시 False
    """
    try:
        mngApi = connApi.api_manager()

        # 연계회원내역조회 쿼리생성
        userInfoQuery = []
        userInfoQuery.append("SELECT")
        userInfoQuery.append("CusNo")
        userInfoQuery.append(", UserId")
        userInfoQuery.append(", PharmAuthFlag")
        userInfoQuery.append(", CustomerAuthFlag")
        userInfoQuery.append(", CONVERT(VARCHAR, PharmAuthDte, 120) AS PharmAuthDte")
        userInfoQuery.append(", CONVERT(VARCHAR, CustomerAuthDte, 120) AS CustomerAuthDte")
        userInfoQuery.append("FROM dbo.DrxsCustomersAuth WITH(NOLOCK)")
        userInfoQueryStr = " ".join(userInfoQuery)

        dbConn = connDb.Manage_logcal_db(iniDatabaseDict['server'], iniDatabaseDict['database'], iniDatabaseDict['username'], iniDatabaseDict['password'], iniDatabaseDict['conntime'] if 'conntime' in iniDatabaseDict else 1800)
        # dbConn = connDb.Manage_logcal_db('localhost\tood2008', 'WithpharmErp', 'sa', '$dnlemvka3300$32!')
        dbConn.conn_open()
        quertResultDf = dbConn.send_query(userInfoQueryStr)
        dbConn.conn_close()

        if type(quertResultDf) == bool and not quertResultDf:
            return False

        # print("##### (send_favority_user_info) quertResultDf :: ", quertResultDf)

        infoDictList = list()
        for idx in range(0, len(quertResultDf)):
            linkUserDict = dict()
            linkUserDict['CusNo'] = quertResultDf.iloc[idx][0]
            linkUserDict['UserId'] = str(quertResultDf.iloc[idx][1])
            linkUserDict['PharmAuthFlag'] = quertResultDf.iloc[idx][2]
            linkUserDict['CustomerAuthFlag'] = quertResultDf.iloc[idx][3]
            linkUserDict['PharmAuthDte'] = quertResultDf.iloc[idx][4]
            linkUserDict['CustomerAuthDte'] = quertResultDf.iloc[idx][5]
            infoDictList.append(linkUserDict)

        # print("##### (send_favority_user_info) infoDictList :: ", infoDictList)

    except Exception as e:
        print("##### (send_favority_user_info) error :: ", e)
        return False
    else:
        if len(infoDictList) > 0:
            datas = dict()
            datas['PHARMACY_IDX'] = userInfoDict['PharmacyIdx']
            datas['DATA_COUNT'] = len(infoDictList)

            items = list()
            for infoDict in infoDictList:
                item = dict()
                item['CusNo'] = infoDict['CusNo']
                item['memberIdx'] = infoDict['UserId']
                item['CustomerAuthFlag'] = infoDict['CustomerAuthFlag']
                item['PharmAuthFlag'] = infoDict['PharmAuthFlag']
                item['CustomerAuthDte'] = infoDict['CustomerAuthDte']
                item['PharmAuthDte'] = infoDict['PharmAuthDte']

                # print("#### (send_favority_user_info) item :: ", item)
                items.append(item)

            datas['ITEMS'] = items
            params = json.dumps(datas)

            checkUrl = iniDrxsDict['apiurl'] + '/setMemberPharmacyLinkStateUpdate_v1.drx'  # 모듈 상태 전송 API
            apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrl, params)  # POST API 로 전송

            if type(apiResultDatas) != dict:
                logger_file.log_error("setMemberPharmacyLinkStateUpdate_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
                return False

            # print("##### (send_favority_user_info) apiResultDatas :: ", apiResultDatas)
        else:
            return

def send_module_error_info(errorFlag, errorMsg):
    """
    에러 내역을 내손안의약국으로 API 전송한다.
    DATE : 22.04.25
    :param errorFlag: 에러상태플래그 (내손내부협의필요)
    :param errorMsg: 에러메시지
    :return: 전송완료시 True, 실패시 False
    """
    try:
        mngApi = connApi.api_manager()

        transDict = dict()
        transDict['PHARMACY_IDX'] = userInfoDict['PharmacyIdx']
        transDict['ERR_TYPE'] = errorFlag
        transDict['DESCRIPTION'] = errorMsg

        transJsonStr = json.dumps(transDict)

        checkUrl = iniDrxsDict['apiurl'] + '/setProcessTransError_v1.drx'  # 모듈 상태 전송 API
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrl, transJsonStr)  # 처방전 POST 방식 전송

        if type(apiResultDatas) != dict:
            logger_file.log_error("setProcessTransError_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
            return False
    except Exception as e:
        print("##### (send_module_error_info) error :: ", e)
        return False
    else:
        if apiResultDatas['Status'] == 'ok':
            return True
        else:
            return False

def send_module_status(statusFlag):
    """
    모듈 상태값을 내손안의약국으로 API 전송한다.
    DATE : 22.04.25
    PARAM : statusFlag(W:대기, R:실행, P중지)
    :return: 전송결과 flag 값, description_str(error시)
    """
    try:
        mngApi = connApi.api_manager()

        transDict = dict()
        transDict['PHARMACY_IDX'] = userInfoDict['PharmacyIdx']
        transDict['STATUS'] = statusFlag

        # print("##### (send_module_status) 모듈 상태값을 전송합니다 상태 :: ", statusFlag)
        transJsonStr = json.dumps(transDict)
        # TODO : 220426 모듈 상태값 전송 API 주소 추가
        checkUrl = iniDrxsDict['apiurl'] + '/setModuleTransState_v1.drx'  # 모듈 상태 전송 API
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrl, transJsonStr)  # 처방전 POST 방식 전송

        if type(apiResultDatas) != dict:
            logger_file.log_error("setModuleTransState_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
            return False, "setModuleTransState_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다."
    except:
        print("##### (send_module_status) error :: {}".format(traceback.format_exc()))
        logger_file.log_error(traceback.format_exc())
        return False, traceback.format_exc()
    else:
        # TODO 220426 : 상태값 전송 결과값 코드에 따라 결과 분기 처리 (ok / error)
        if 'Status' in apiResultDatas and apiResultDatas['Status'] == 'error':
            logger_api.send_api_log('', '', str(userInfoDict['PharmacyIdx']), 'ERR-201', '(send_module_status) API SEND ERROR (STATUS : {})'.format(apiResultDatas['Status']))
            return False, 'DRxS_API 서버 호출 HTTP Status 값이 200이 아닙니다.'
        else:
            logger_file.log_info("##### PHARMACY_IDX : {} 모듈실행 상태정보 발송완료".format(transDict['PHARMACY_IDX']))
            return True, '성공'

def clear_prescription_info():
    """
    처방전달시스템의 과거 미처리 데이터를 조회하고 초기화 처리한 뒤, 처리내역을 API로 전송한다.
    :return:
    """
    try:
        global prescription_clear_flag
        if prescription_clear_flag == 'Y':      # 이미 처리한 경우 미처리
            return

        # dbconnection 생성
        dbConn = connDb.Manage_logcal_db(iniDatabaseDict['server'], 'WithpharmDrx', '', '', iniDatabaseDict['conntime'] if 'conntime' in iniDatabaseDict else 1800)

        # 약국 DB 내 미처리 된 처방전 정보 조회 (1주일)
        tempQuery = []
        tempQuery.append('SELECT QrNm, QrcodeIdx, UserIdx, PrescriptionMainIdx, PharmacyIdx, Flag, RegDt ')
        tempQuery.append('FROM WithpharmDrx.dbo.DrxQr1 ')
        tempQuery.append('WHERE 1=1 ')
        tempQuery.append("AND Flag = '0' ")
        tempQuery.append('AND RegDt = CONVERT(CHAR(10), DATEADD(DAY, -7, GETDATE()), 23)')
        sendSql = " ".join(tempQuery)

        dbConn.conn_open()
        select_qr_result = dbConn.send_query(sendSql)       # 1주일 전 취소 대상 데이터 조회
        dbConn.conn_close()

        if type(select_qr_result) == bool and not select_qr_result:
            return False

        # print("# 미처리 데이터 내역 :: {}".format(select_qr_result))
        # print("# 미처리 데이터 갯수 :: {}".format(select_qr_result))

        # 미처리 데이터가 존재하지않을 경우 리턴처리
        if isinstance(select_qr_result, pd.DataFrame) and select_qr_result.empty:
            # print("미 처리 된 과거 처방전 내역이 존재하지 않습니다.")
            return

        # 검색 결과 데이터 정렬 (API 전송용)
        select_data_list = []
        qrnm_str = ""       # UPDATE IN 쿼리용 QrNm Str
        header_dict = dict()
        header_dict['pharmacy-idx'] = userInfoDict['PharmacyIdx']
        header_dict['clear-datetime'] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        for item in select_qr_result.iterrows():
            data_dict = dict()
            data_dict['qrcode-idx'] = str(item[1]['QrcodeIdx'])
            data_dict['member-idx'] = str(item[1]['UserIdx'])
            data_dict['flag'] = str(item[1]['Flag'])

            select_data_list.append(data_dict)

            qrnm_str += "'" + str(item[1]['QrNm']) + "',"   # UPDATE IN 조건 쿼리용 QrNm문자열

        qrnm_str = qrnm_str[:-1]        # UPDATE 쿼리용 QrNm 마지막 콤마 제거
        header_dict['items'] = select_data_list
        # print("## header_dict :: {}".format(header_dict))

        # 조회 내역 초기화 업데이트 처리
        # DrxQr3 이미지 정보 초기화 쿼리 생성
        update3_query = []
        update3_query.append('UPDATE WithpharmDrx.dbo.DrxQr3 ')
        update3_query.append("SET PrescriptionImage = CONVERT(varbinary(max),''), SysDte = GETDATE() ")
        update3_query.append("WHERE 1=1 AND QrNm IN ({})".format(qrnm_str))
        send3Sql = " ".join(update3_query)

        # DrxQr1 데이터 플래그 초기화 쿼리 생성
        update1_query = []
        update1_query.append('UPDATE WithpharmDrx.dbo.DrxQr1 ')
        update1_query.append("SET Flag = '6', SysDte = GETDATE() ")
        update1_query.append("WHERE 1=1 AND QrNm IN ({})".format(qrnm_str))
        send1Sql = " ".join(update1_query)

        # print("send1Sql :: {}".format(send1Sql))
        # print("send3Sql :: {}".format(send3Sql))
        # 쿼리 실행 및 결과 카운트 계산
        dbConn.conn_open()
        update3_qr_result = dbConn.send_query_update(send3Sql)  # qr3 1주일 전 취소 대상 데이터 초기화
        # print("# update3_qr_result :: {}".format(update3_qr_result))
        dbConn.conn_close()

        if type(update3_qr_result) == str and update3_qr_result == "DB_SEND_QUERY_ERROR":
            return False

        if type(update3_qr_result) == str and str(update3_qr_result) == 'DB_SEND_QUERY_ERROR':
            # error 처리
            print("# DrxQr3 Update Error")
            return False

        dbConn.conn_open()
        update1_qr_result = dbConn.send_query_update(send1Sql)  # qr1 1주일 전 취소 대상 데이터 초기화
        # print("# update1_qr_result :: {}".format(update1_qr_result))
        dbConn.conn_close()

        if type(update1_qr_result) == str and str(update1_qr_result) == 'DB_SEND_QUERY_ERROR':
            # error 처리
            print("# DrxQr1 Update Error")

        # 조회 내역 API 전송
        # 1. select_data_list 를 json 변환 처리
        select_data_list_json = json.dumps(header_dict)        # TODO : 조회 데이터를 API 전송 포맷으로 변경한 뒤 json 처리 해야함
        enc_datas = common_process.common_process().proc_pip_encrypt(select_data_list_json)
        send_data_json = common_process.common_process().proc_packing_drxs(enc_datas)

        print("# 미처리데이터 전송 API 최종 {}".format(send_data_json))
        # 2. 자체 암호화 처리 후 내손안의약국 API 전송 {"drxs" : "암호화데이터"}
        cancel_data_api = iniDrxsDict['api-drv']
        post_headers = {'Content-Type': 'application/json', 'charset': 'utf-8', 'X-API-TYPE': 'setUserPrescriptionWeekReceptionInit'}
        response_api = requests.post(cancel_data_api, data=send_data_json, headers=post_headers)

        if response_api.status_code != 200:
            # API 전송 에러 오류처리
            err_send_data = common_process.common_process().proc_error_return_func('ERROR', '', 'PWI-103')
            print("(ERROR) 최종 리턴데이터 :: {}".format(err_send_data))
            return err_send_data

    except BaseException as e:
        print(traceback.format_exc())
        # 오류코드 정의 필요
        err_send_data = common_process.common_process().proc_error_return_func('ERROR', '', 'PWI-103')
        print("(ERROR) 최종 리턴데이터 :: {}".format(err_send_data))
        return err_send_data
    else:
        print("## 미처리 처방전 QR 데이터 초기화 처리 완료")
        prescription_clear_flag = 'Y'
        dbConn = None
        return


##########################################################################################
####### 요청부 (위드팜)
##########################################################################################
def request_server_part(gui_root):
    """
    서버 요청부 파트
    favoritUser?PharmName=강진약국&PharmNo=1234567890&SaupNo=1234578901
    :return:
    """
    gui_root.textInsert("위드팜 처방전 연계 요청부 프로세스를 수행합니다.")
    # common_log = commonCode.commonLog(userInfoDict['pharmNo'], userInfoDict['saupNo'], userInfoDict['PharmacyIdx'])

    # API 클래스 생성
    mngApi = connApi.api_manager()
    # WithpharmErp (처방전, 회원) WithpharmDrxs (회원연계확인, 전송조제내역저장, QR처방전)
    dbConn = connDb.Manage_logcal_db(iniDatabaseDict['server'], iniDatabaseDict['database'], iniDatabaseDict['username'], iniDatabaseDict['password'], iniDatabaseDict['conntime'] if 'conntime' in iniDatabaseDict else 1800)
    # dbConn = connDb.Manage_logcal_db('localhost\tood2008', 'WithpharmErp', 'sa', '$dnlemvka3300$32!')

    # 약국회원정보를 이용하여 회원약국의 내손안의약국 단골회원을 조회한다.
    # print("##### 약국회원정보 :: ", userInfoDict)

    # TODO 231004 GET방식 API POST방식 + 암호화 전환으로인해 데이터 변환
    send_body_data = dict()
    send_body_data['PharmacyIdx'] = str(userInfoDict['PharmacyIdx'])
    send_body_data['PharmNo'] = str(userInfoDict['pharmNo'])
    send_body_data['SaupNo'] = str(userInfoDict['saupNo'])

    gui_root.textInsert("내손안의약국 단골회원정보를 요청합니다.")
    checkUrl = iniDrxsDict['apiurl'] + '/favoritUserList_v1.drx'
    # print("##### checkUrl :: ", checkUrl)
    userInfoKey, userInfoList = mngApi.api_conn_post(checkUrl, json.dumps(send_body_data))

    if type(userInfoList) != dict:
        logger_file.log_error("favoritUserList_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
        return False

    # API 발송 오류일 경우
    if type(userInfoKey) == bool and not userInfoKey and type(userInfoList) == str:
        logger_file.log_error("단골회원목록요청 API에서 에러를 리턴하여 해당 사이클은 수행하지않습니다.")
        logger_file.log_error("## (favoritUserList.drx) API ERROR :: {}".format(userInfoList))
        return False
        # logger_api.send_api_log(userInfoDict['pharmNo'], userInfoDict['saupNo'], userInfoDict['PharmacyIdx'], 'ERR-201', '(favoritUserList.drx) API SEND ERROR')



    # print("##### 연계대상목록요청정보키(userInfoKey) :: ", userInfoKey)
    # print("##### 연계대상목록요청정보(userInfoList) :: ", userInfoList)
    # print("##### 연계대상목록요청정보갯수(userInfoList.count) :: ", userInfoList['DataCount'])

    # logger_file.log_info("##### 연계대상목록요청정보(userInfoList) :: {}".format(userInfoList))
    # logger_file.log_info("##### 연계대상목록요청정보 대상수(userInfoList.count) :: {}".format(userInfoList['DataCount']))

    # 필요 변수 생성
    sameUserList = []       # 동명이인 내역
    resultUserList = []     # 최종 전송 결과 유저

    if len(userInfoList['Items']) == 0:
        gui_root.textInsert("단골회원정보가 존재하지 않습니다.")
        logger_file.log_info("약국의 단골회원 정보가 존재하지않습니다.")
        # common_class.send_api_log(organ_number=str(userInfoDict['pharmNo']), biz_number=str(userInfoDict['saupNo']), pharmacy_idx=str(userInfoDict['PharmacyIdx']), err_code='ERR-100', err_msg='NOT_FAVORITY_MEMBER_INFO')
        return "EMPTY_FAVORITY_MEMBER"

    # TODO 230313 : TASK. 특정 플래그가 들어왔을 경우, 단골회원정보의 CI를 업데이트 처리한다. ( 1회성으로만 진행.. 연계대상 회원목록 루프안에서 진행 )
    if str(iniDrxsDict['ci-update']) == 'N':
        logger_file.log_info("### 1회성 CI 정보 업데이트를 수행합니다 (v2.0 이전 회원 CI 연계용)")
        # CI 정보 업데이트 처리
        for item in userInfoList['Items']:  # items 내 값 추출
            dbConn.conn_open()
            dbConn.update_ci_query(item)
            dbConn.conn_close()

        # CI 업데이트 완료 후 ini 변경 및 ini-dict 변경
        iniMng.write_ini_file('DRXS', 'ci-update', 'Y')
        iniDrxsDict['ci-update'] = 'Y'

        # SMS-CI 공백 데이터 삭제 로직
        dbConn.conn_open()
        dbConn.delete_ci_query()
        dbConn.conn_close()
        logger_file.log_info("1회성 CI 정보 업데이트를 완료하였습니다.")


    global prescription_mapping_flag
    # print("prescription_mapping_flag :: ", prescription_mapping_flag)

    if prescription_mapping_flag == 'N':
        logger_file.log_info("연계조제내역 중 삭제처리가된 데이터를 조회합니다. (삭제된 데이터를 조회하여 DRxS 조제내역과 매핑)")
        # print("조제내역 삭제내역 매핑 데이터를 조회합니다.")

        # 조제내역 삭제내역 매핑 조회
        pre_mapping_list = []
        pre_mapping_list.append("SELECT DPL.CusNo, DPL.UserId, DPL.PrescriptionCd, PRE.DelYn, PRE.MDte")
        pre_mapping_list.append("FROM WithpharmDrx.dbo.DrxsPrescriptionLinkInfo AS DPL")
        pre_mapping_list.append("INNER JOIN WithpharmErp.dbo.Prescription AS PRE")
        pre_mapping_list.append("ON DPL.PrescriptionCd = PRE.PrescriptionCd")
        pre_mapping_list.append("WHERE 1=1")
        pre_mapping_list.append("AND PRE.DelYn = 'Y'")
        pre_mapping_list.append("AND CONVERT(VARCHAR, DPL.TransDt, 23) BETWEEN CONVERT(VARCHAR, DATEADD(DAY, -3, GETDATE()), 23) AND GETDATE()")

        pre_mapping_sql = " ".join(pre_mapping_list)

        dbConn.conn_open()
        pre_mapping_sql_result = dbConn.send_query(pre_mapping_sql)
        dbConn.conn_close()

        if type(pre_mapping_sql_result) == bool and not pre_mapping_sql_result:
            return False

        if type(pre_mapping_sql_result) != bool and pre_mapping_sql_result.empty:
            logger_file.log_info("연계된 조제내역중 약국DB에 삭제처리된 데이터가 존재하지않습니다.")
            print("전송완료한 조제내역중 삭제처리된 데이터가 존재하지않습니다.")
            # common_class.send_api_log(organ_number=str(userInfoDict['pharmNo']), biz_number=str(userInfoDict['saupNo']),
            #                           pharmacy_idx=str(userInfoDict['PharmacyIdx']), err_code='SUC-100',
            #                           err_msg='DELETE_PRESCRIPTION_NOT_FOUND')
            prescription_mapping_flag = 'Y'
        else:
            # 삭제처리된 조제내역 데이터 키 API 전송
            logger_file.log_info("전송완료한 조제내역중 삭제처리된 조재내역이 존재합니다. 해당 조제내역 정보 전송을 수행합니다.")
            pre_mapping_sql_result_dict = pre_mapping_sql_result.to_dict()
            print("전송완료한 조제내역중 삭제처리된 데이터가 존재합니다. :: {}".format(pre_mapping_sql_result_dict))
            result_flag = send_prescription_mapping(pre_mapping_sql_result_dict, str(userInfoDict['PharmacyIdx']), mngApi)

            if result_flag == True:
                logger_file.log_info("전송완료한 조제내역중 삭제처리된 조제내역 API 전송 완료")
                print("## (삭제 처방전 정보 전달) 삭제 처방전 조제정보 API 발송 완료")
                prescription_mapping_flag = 'Y'
            else:
                logger_file.log_info("전송완료한 조제내역중 삭제처리된 조제내역 API 전송 실패")
                print("## (삭제 처방전 정보 전달) 삭제 처방전 조제정보 API 발송 실패")
                prescription_mapping_flag = 'N'
        # print("## 전송완료 조제내역중 삭제처리데이터 전송처리 완료 :: prescription_mapping_flag :: {}".format(prescription_mapping_flag))
    else:
        print("조제내역 삭제내역 매핑 데이터를 조회X")

    print("## 연계검증대상 회원 수 :: {}".format(len(userInfoList['Items'])))
    # 연계대상 회원목록 루프돌며 동명이인 검증 및 약국 연계 승인 여부 검증
    for item in userInfoList['Items']:  # items 내 값 추출
        # 생년월일이 8자리일경우 6자리로 변경
        if len(item['birth']) == 8:
            temp = item['birth']
            item['birth'] = temp[2:]

        # logger_file.log_info("### {} 회원의 동명이인검증 및 조제내역연계 승인여부를 검증합니다.".format(str(item['user_name'])))

        # TODO 230328 ci에 해당하는 AUTH USER정보의 CusJmno를 이용하여 PatientCustomer테이블에 유저가 존재하는지 조회(방문이력있는회원인지), 데이터가 있을 경우 CusNo를 업데이트처리한다.
        # TODO 241121 CI로 인해 암호문이 길어져 memory error 발생하므로 CI를 제외하고 진행
        # if str(item['sms_ci']) != '':
        #     select_auth1_query_list = []
        #     select_auth1_query_list.append("SELECT TOP 1 CusNo, UserId, PharmAuthFlag, CustomerAuthFlag, UserSmsCi, CusJmno From WithpharmDrx.dbo.DrxsCustomersAuth WITH(NOLOCK)")
        #     select_auth1_query_list.append(" WHERE 1=1 AND UserSmsCi = '" + str(item['sms_ci']) + "'")
        #     select_auth1_query = " ".join(select_auth1_query_list)
        #
        #     dbConn.conn_open()
        #     # 단골회원의 AUTH 테이블 정보 유무 조회
        #     select_auth1_query_result = dbConn.send_query(select_auth1_query)
        #     dbConn.conn_close()
        #
        #     if type(select_auth1_query_result) == bool and not select_auth1_query_result:
        #         return False
        #
        #
        #     if type(select_auth1_query_result) != bool and select_auth1_query_result.empty:     # 데이터 미 존재 시 PASS
        #         # print("해당 회원은 약국방문이력이 존재하지않습니다.")
        #         # logger_file.log_info("### {} 회원은 약국방문이력이 존재하지않습니다. (AUTH 미존재)")
        #         gui_root.textInsert(str(item['user_name'] + " 회원은 AUTH1 미존재"))
        #     else:       # 데이터 존재 시 CusNo가 있으면 pass, CusNo가 없으면 CusNo 조회 후 UPDATE AUTH CusNo
        #         select_auth1_query_result_dict = select_auth1_query_result.to_dict()
        #         if str(select_auth1_query_result_dict['CusNo'][0]) != '' and str(select_auth1_query_result_dict['CusNo'][0]) != None:
        #             # 이미 승인 완료된 회원이므로 continue 처리
        #             print("해당 회원은 이미 승인이 완료된 회원입니다.")
        #         else:   # CusNo가 없으므로 CusJmno를 이용하여 PatientCustomer 조회
        #             # 주민번호(CusJmno)가 존재하면 PatientCustomers - CusNo 조회
        #             if str(select_auth1_query_result_dict['CusJmno'][0]) != '' and str(select_auth1_query_result_dict['CusJmno'][0]) != None:
        #                 select_patient_user_list = []
        #                 select_patient_user_list.append("SELECT TOP 1 CusNo, CusNm, CusJmno, RealBirth, Sex FROM WithpharmErp.dbo.PatientCustomers")
        #                 select_patient_user_list.append("WHERE 1=1")
        #                 select_patient_user_list.append("AND CusJmno = '" + str(select_auth1_query_result_dict['CusJmno'][0]) + "'")
        #
        #                 select_patient_user_query = " ".join(select_patient_user_list)
        #
        #                 dbConn.conn_open()
        #                 # 단골회원의 PatientCustomers 테이블 정보 유무 조회
        #                 select_patient_user_query_result = dbConn.send_query(select_patient_user_query)
        #                 dbConn.conn_close()
        #
        #                 if type(select_patient_user_query_result) == bool and not select_patient_user_query_result:
        #                     return False
        #
        #                 # if select_patient_user_query_result.empty:
        #                 #     print("PatientCustomers 회원정보가 존재하지않습니다.")
        #
        #                 select_patient_user_query_result_dict = select_patient_user_query_result.to_dict()
        #                 print("## (select_patient_user_query_result_dict) :: {}".format(select_patient_user_query_result_dict))
        #
        #                 # PatientCustomers 에 회원정보 존재 시 Auth UPDATE
        #                 if len(select_patient_user_query_result_dict['CusNo']) > 0:
        #                 # if str(select_patient_user_query_result_dict['CusNo'][0]) != '' and str(select_patient_user_query_result_dict['CusNo'][0]) != None:
        #                 #     logger_file.log_info("### 검증된 회원( {} )의 정보를 AUTH 테이블에 업데이트 처리합니다.".format(str(item['user_name'])))
        #
        #                     update_auth_user_list = []
        #                     update_auth_user_list.append("UPDATE WithpharmDrx.dbo.DrxsCustomersAuth SET")
        #                     update_auth_user_list.append("CusNo = '" + str(select_patient_user_query_result_dict['CusNo'][0]) + "'")
        #                     update_auth_user_list.append(", PharmAuthFlag = 'Y'")
        #                     update_auth_user_list.append(", CustomerAuthFlag = 'Y'")
        #                     update_auth_user_list.append("WHERE 1=1")
        #                     update_auth_user_list.append("AND CusJmno = '" + str(select_auth1_query_result_dict['CusJmno'][0]) + "'")
        #
        #                     update_auth_user_query = " ".join(update_auth_user_list)
        #
        #                     dbConn.conn_open()
        #                     update_count = dbConn.cursor.execute(update_auth_user_query)
        #                     dbConn.conn.commit()
        #                     dbConn.conn_close()
        #
        #             else:   # CusNo도 미존재, CusJmno도 미존재 (v1.5 회원) TODO 이경우는 어떻게? 사전인증을 하지않고, 단골약국만 추가한경우
        #                 logger_file.log_info("### {} 회원은 사전인증없이 단골약국만 추가한 회원입니다. CI 업데이트가 필요합니다.".format(str(item['user_name'])))
        #                 print("사전인증을 하지않고, 단골약국만 추가한경우")

        # TODO 230313 : CI-UPDATE Flag를 확인하여 해당 UserId(MemberIdx)에 해당하는 고객정보의 CI를 업데이트 처리한다.

        print("##### 내손안의약국 회원(" + item['user_name'] + ")님의 약국고객여부를 판별합니다.")
        # 내손안의약국 회원의 CI 정보를 활용하여 약국 고객 확인
        tempQuery = []
        tempQuery.append('SELECT TOP 1 PC.CusNo, PC.FamNo, PC.CusNm, PC.CusJmno, PC.RealBirth, PC.Sex')
        tempQuery.append(', PC.HpTel, PC.CertiNo, DCA.CustomerAuthFlag, DCA.PharmAuthFlag')
        tempQuery.append(', CONVERT(VARCHAR, DCA.CustomerAuthDte, 120) AS CustomerAuthDte')
        tempQuery.append(', CONVERT(VARCHAR, DCA.PharmAuthDte, 120) AS PharmAuthDte')
        # tempQuery.append(', DCA.UserSmsCi')
        tempQuery.append(', DCA.CusJmno AS UserJmno')
        tempQuery.append(', CONVERT(VARCHAR, DCA.UserSmsCiDte, 120) AS UserSmsCiDte')
        tempQuery.append(', CONVERT(VARCHAR, DCA.PharmAuthAutoDte, 120) AS PharmAuthAutoDte')
        tempQuery.append('FROM WithpharmErp.dbo.PatientCustomers AS PC WITH(NOLOCK)')
        tempQuery.append('INNER JOIN WithpharmDrx.dbo.DrxsCustomersAuth AS DCA WITH(NOLOCK) ON DCA.CusNo = PC.CusNo')
        tempQuery.append('WHERE 1=1')
        # tempQuery.append("AND DCA.CusNo = '" + quertResultDf.iloc[0][0] + "'")
        tempQuery.append("AND DCA.UserId = '" + item['idx'] + "'")
        # tempQuery.append("AND DCA.UserSmsCi = '" + item['sms_ci'] + "'")        # TODO 230309 : 기존 1.5버전의 고객중 CI가 업데이트되지않은(픽업서비스 미사용) 고객은 빠질듯 (약국 방문시 CI없는 회원의 업데이트 필요)
        # TODO 241221 sms-ci로 인해 memory error 발생하여 sms-ci 없이 단골고객list와 AUTH1 비교 후 연계 진행하도록 변경한다. (기존 1.5버전 고객은 ci 비교 없이 수용하는걸로 내부정책결정)
        sendSql = " ".join(tempQuery)
        dbConn.conn_open()
        quertResultDf = dbConn.send_query(sendSql)
        dbConn.conn_close()
        
        if type(quertResultDf) == bool and not quertResultDf:
            # DB Connectrion Error 일 경우에는 Continue 하지않는다
            return False

        if type(quertResultDf) != bool and quertResultDf.empty:
            # logger_file.log_info("### {} 회원은 약국방문이력이 존재하지않은 회원입니다(연계데이터 미존재)".format(str(item['user_name'])))
            print(str(item['user_name'] + " 회원은 약국방문이력이 존재하지않은 회원입니다."))
            gui_root.textInsert(str(item['user_name'] + " 회원은 약국방문이력이 존재하지않은 회원입니다."))
            continue
        elif type(quertResultDf) == bool and not quertResultDf:
            # TODO 240104 동명이인검증시 쿼리오류발생에 break처리인가 continue 인가?
            break


        # 개별로 연계대상회원이 약국 로컬 DB에 존재하는지 확인 (221103 주석)
        # gui_root.textInsert(str(item['user_name']+" 회원의 본인여부를 판별합니다."))
        # # gui_root.textInsert()
        # userInfoQuery = []
        # userInfoQuery.append("SELECT")
        # userInfoQuery.append("CusNo")
        # userInfoQuery.append(", FamNo")
        # userInfoQuery.append(", CusNm")
        # userInfoQuery.append(", CusJmno")
        # userInfoQuery.append(", RealBirth")
        # userInfoQuery.append(", Sex")
        # userInfoQuery.append(", HpTel")
        # userInfoQuery.append(", CertiNo")
        # userInfoQuery.append("FROM dbo.PatientCustomers")
        # userInfoQuery.append("WHERE RealBirth = '"+item['birth']+"'")
        # userInfoQuery.append("AND CusNm = '"+item['user_name']+"'")
        # userInfoQuery.append("AND Sex = '"+item['sex']+"'")
        # userInfoQueryStr = " ".join(userInfoQuery)ekswkd
        #
        # dbConn = connDb.Manage_logcal_db(iniDatabaseDict['server'], iniDatabaseDict['database'], iniDatabaseDict['username'], iniDatabaseDict['password'])
        # dbConn.conn_open()
        # quertResultDf = dbConn.send_query(userInfoQueryStr)
        # dbConn.conn_close()
        # print("##### 회원 존재 여부 결과 :: \n", quertResultDf)
        # print("##### 회원 존재 여부 결과 갯수 :: \n", len(quertResultDf))
        # 비교 후 데이터가 있는 df의 경우 별도로 저장해둘것 (회원여부판별)

        # print("##### quertResultDf :: ", quertResultDf)
        # print("##### quertResultDf.iloc[0][0] CusNo :: ", quertResultDf.iloc[0][0])
        # print("##### quertResultDf.iloc[0][1] FamNo :: ", quertResultDf.iloc[0][1])
        # print("##### quertResultDf.iloc[0][2] CusNm :: ", quertResultDf.iloc[0][2])
        # print("##### quertResultDf.iloc[0][3] CusJmno :: ", quertResultDf.iloc[0][3])
        # print("##### quertResultDf.iloc[0][4] RealBirth :: ", quertResultDf.iloc[0][4])
        # print("##### quertResultDf.iloc[0][5] Sex :: ", quertResultDf.iloc[0][5])
        # 
        # print("##### quertResultDf.iloc[0][6] HpTel :: ", quertResultDf.iloc[0][6])
        # print("##### quertResultDf.iloc[0][7] CertiNo :: ", quertResultDf.iloc[0][7])
        # print("##### quertResultDf.iloc[0][8] CustomerAuthFlag :: ", quertResultDf.iloc[0][8])
        # print("##### quertResultDf.iloc[0][9] PharmAuthFlag :: ", quertResultDf.iloc[0][9])
        # print("##### quertResultDf.iloc[0][10] CustomerAuthDte :: ", quertResultDf.iloc[0][10])
        # print("##### quertResultDf.iloc[0][11] PharmAuthDte :: ", quertResultDf.iloc[0][11])
        # print("##### quertResultDf.iloc[0][12] UserSmsCi :: ", quertResultDf.iloc[0][12])
        # print("##### quertResultDf.iloc[0][13] UserSmsCiDte :: ", quertResultDf.iloc[0][13])
        # print("##### quertResultDf.iloc[0][14] PharmAuthAutoDte :: ", quertResultDf.iloc[0][14])

        # 아래 조건절 제외하고 연계회원정보 추가 로직 이동 (221103 수정)
        compUserInfoDict = dict()
        compUserInfoDict['CusNo'] = quertResultDf.iloc[0][0]
        compUserInfoDict['FamNo'] = quertResultDf.iloc[0][1]
        compUserInfoDict['CusNm'] = quertResultDf.iloc[0][2]
        compUserInfoDict['CusJmno'] = quertResultDf.iloc[0][3]
        compUserInfoDict['RealBirth'] = quertResultDf.iloc[0][4]
        compUserInfoDict['Sex'] = quertResultDf.iloc[0][5]
        compUserInfoDict['HpTel'] = quertResultDf.iloc[0][6]
        compUserInfoDict['CertiNo'] = quertResultDf.iloc[0][7]
        compUserInfoDict['CustomerAuthFlag'] = quertResultDf.iloc[0][8]
        compUserInfoDict['PharmAuthFlag'] = quertResultDf.iloc[0][9]
        compUserInfoDict['CustomerAuthDte'] = quertResultDf.iloc[0][10]
        compUserInfoDict['PharmAuthDte'] = quertResultDf.iloc[0][11]
        # DrxsCustomersAuth 신규 추가 필드
        compUserInfoDict['UserSmsCi'] = quertResultDf.iloc[0][12]
        compUserInfoDict['UserSmsCiDte'] = quertResultDf.iloc[0][13]
        compUserInfoDict['PharmAuthAutoDte'] = quertResultDf.iloc[0][14]
        compUserInfoDict['UserId'] = item['idx']
        compUserInfoDict['UserName'] = item['user_name']
        compUserInfoDict['Mobile'] = item['mobile']
        compUserInfoDict['birth'] = item['birth']
        compUserInfoDict['regi_date'] = item['regi_date']
        # compUserInfoDict['sms_ci'] = item['sms_ci']     # 221116 CI 정보 제외 버전
        # logger_file.log_info("### 최종연계대상회원정보를 저장합니다. :: {}".format(str(compUserInfoDict)))
        userInfoListGlobal.append(compUserInfoDict)

        # 단일로 검증된 연계회원정보를 최종연계 대상 리스트에 추가 resultUserList
        resultUserList.append(quertResultDf.to_dict())
        # 여기까지 CI를 이용한 회원 인증 로직 END

        # if quertResultDf.empty:
        #     print(str(item['user_name'] + " 회원은 약국방문이력이 존재하지않은 회원입니다."))
        #     gui_root.textInsert(str(item['user_name']+" 회원은 약국방문이력이 존재하지않은 회원입니다."))
        #     continue
        #
        # # 회원정보가 존재하지만 동명이인이고 생년월일과 성별까지 같을 경우 결과값이 1보다 크므로 해당 인원은 제외 (221103 주석)
        # # TODO 이름, 생년월일, 성별까지 같은 사용자의 경우 판별할 수 없으므로 해당인원의 연계는 제한한다, 수동으로 DB 확인 후 처리하도록 한다.
        # if len(quertResultDf) > 1:
        #     print("##### (요청부) 연계회원 중 동명이인 회원이 존재합니다. 해당정보를 제외하고 연계회원을 구축합니다.")
        #     gui_root.textInsert(str(item['user_name']+" 회원은 동명이인 정보가 조회되어 최종연계회원에서 제외합니다."))
        #     # 220310 수정 len(quertResultDf) -> range(0, len(quertResultDf))
        #     for idx in range(0, len(quertResultDf)):
        #         sameUserDict = dict()
        #         sameUserDict['CusNo'] = quertResultDf.iloc[idx][0]
        #         sameUserDict['FamNo'] = quertResultDf.iloc[idx][1]
        #         sameUserDict['CusNm'] = quertResultDf.iloc[idx][2]
        #         sameUserDict['CusJmno'] = quertResultDf.iloc[idx][3]
        #         sameUserDict['RealBirth'] = quertResultDf.iloc[idx][4]
        #         sameUserDict['Sex'] = quertResultDf.iloc[idx][5]
        #         sameUserDict['CertiNo'] = quertResultDf.iloc[idx][7]
        #         sameUserDict['UserId'] = item['idx']
        #         sameUserDict['UserName'] = item['user_name']
        #         sameUserDict['Mobile'] = item['mobile']
        #         sameUserDict['birth'] = item['birth']
        #         sameUserDict['regi_date'] = item['regi_date']
        #         sameUserList.append(sameUserDict)
        #         # TODO 221031 동명이인이라도 기존에 연계된 내역 혹은, 연계승인 플래그가 YY혹은 YN으로 존재할 경우 해당 인원은 연계를 수행하게끔 변경한다.
        #
        #
        # # 일반회원의 내손안의 약국 승인정보 존재여부 확인 SELECT (221103 주석)
        # print("##### 연계 예정 회원("+quertResultDf.iloc[0][2]+")님의 연계승인정보를 조회합니다.")
        # dbConn.conn_open()
        # tempQuery = []
        # tempQuery.append('SELECT CusNo, PharmAuthFlag, CustomerAuthFlag FROM dbo.DrxsCustomersAuth')
        # tempQuery.append("WHERE CusNo = '" + quertResultDf.iloc[0][0] + "'")
        # sendSql = " ".join(tempQuery)
        # queryResult = dbConn.send_query(sendSql)
        # dbConn.conn_close()
        #
        # if len(queryResult) == 0:
        #     # 신규연계회원 회원의 연계승인 플래그 최초저장
        #     gui_root.textInsert(str("신규연계회원("+quertResultDf.iloc[0][2]+")님의 연계신청정보를 데이터베이스에 저장합니다."))
        #     print("##### 신규연계회원("+quertResultDf.iloc[0][2]+")님의 플래그정보를 INSERT 처리합니다.")
        #     dbConn.conn_open()
        #     tempQuery = []
        #     tempQuery.append(quertResultDf.iloc[0][0])
        #     tempQuery.append(item['idx'])
        #     tempQuery.append('Y')
        #     queryResult = dbConn.send_query_authinfo_insert(tempQuery)
        #     dbConn.conn_close()
        # elif len(queryResult) == 1:
        #     # TODO : 기존연계회원 회원의 약국연계승인 플래그 검증 (완료)
        #     print("##### 기존연계회원("+quertResultDf.iloc[0][2]+")님의 플래그정보를 검증 처리합니다.")
        #     gui_root.textInsert(str("기존연계회원(" + quertResultDf.iloc[0][2] + ")님의 연계신청정보를 검증 처리합니다."))
        #     if queryResult.iloc[0][1] == None:
        #         # TODO : 기존연계회원 회원의 약국연계승인 플래그 미존재시 처방전 연계 회원목록으로 추가하지않음 (완료)
        #         print("##### 기존연계회원("+quertResultDf.iloc[0][2]+")님은 약사님의 연계승인이 이뤄지지 않았습니다.")
        #         gui_root.textInsert(str("기존연계회원("+quertResultDf.iloc[0][2]+")님은 약국의 연계승인이 이뤄지지 않았습니다."))
        #         gui_root.textInsert(str("기존연계회원(" + quertResultDf.iloc[0][2] + ")님의 처방전 연계승인을 진행해주세요. <청구SW-코드관리-환경설정-내손안의약국 고객인증>"))
        #         continue
        #     elif queryResult.iloc[0][1] == 'Y' or queryResult.iloc[0][1] == 'y':
        #         # TODO : 기존연계회원 회원의 약국연계승인완료시 회원정보(휴대전화번호)업데이트 및 처방전 연계 최종대상으로 추가 (완료)
        #         print("##### 기존연계회원(" + quertResultDf.iloc[0][2] + ")님은 약사님의 연계승인이 완료되었습니다.")
        #         gui_root.textInsert(str("기존연계회원(" + quertResultDf.iloc[0][2] + ")님은 약사님의 연계승인이 완료되었습니다."))
        #
        #         print("##### 기존연계회원(" + quertResultDf.iloc[0][2] + ")님의 회원정보를 로컬DB에 업데이트 처리합니다.")
        #         gui_root.textInsert(str("기존연계회원(" + quertResultDf.iloc[0][2] + ")님의 회원정보를 로컬DB에 업데이트 처리합니다."))
        #
        #         # 모바일 정보 업데이트 (위드팜에서 정보업데이트 보류 요청으로 주석)
        #         # tempMobile = item['mobile']
        #         # print("##### 기존연계회원(" + quertResultDf.iloc[0][2] + ")님의 휴대전화번호 파싱 : ", tempMobile[0:3]+"-"+tempMobile[3:7]+"-"+tempMobile[7:])
        #         # dbConn.conn_open()
        #         # tempQuery = []
        #         # tempQuery.append(tempMobile)
        #         # tempQuery.append(quertResultDf.iloc[0][0])
        #         # queryResult = dbConn.send_query_userinfo_update(tempQuery)
        #         # dbConn.conn_close()
        #
        #         # 검증완료된 유저정보 저장, 단일1인일 경우(전역변수)
        #         compUserInfoDict = dict()
        #         compUserInfoDict['CusNo'] = quertResultDf.iloc[0][0]
        #         compUserInfoDict['FamNo'] = quertResultDf.iloc[0][1]
        #         compUserInfoDict['CusNm'] = quertResultDf.iloc[0][2]
        #         compUserInfoDict['CusJmno'] = quertResultDf.iloc[0][3]
        #         compUserInfoDict['RealBirth'] = quertResultDf.iloc[0][4]
        #         compUserInfoDict['Sex'] = quertResultDf.iloc[0][5]
        #         compUserInfoDict['UserId'] = item['idx']
        #         compUserInfoDict['UserName'] = item['user_name']
        #         compUserInfoDict['Mobile'] = item['mobile']
        #         compUserInfoDict['birth'] = item['birth']
        #         compUserInfoDict['regi_date'] = item['regi_date']
        #         userInfoListGlobal.append(compUserInfoDict)
        #         print("userInfoListGlobal 데이터 추가")
        #         # 단일로 검증된 연계회원정보를 최종연계 대상 리스트에 추가 resultUserList
        #         resultUserList.append(quertResultDf.to_dict())

    # logger_file.log_info("### 최종 처방전 연계승인 회원 수 :: {}".format(len(resultUserList)))
    print("##### 최종 처방전 연계 승인 회원 수 :: ", len(resultUserList))
    # print("##### 최종 처방전 연계승인 회원 정보 :: ")

    # print("동명이인 정보를 출력합니다.")
    # print(sameUserList)
    # print("동명이인 정보를 API 전송합니다.")

    # 221103 주석
    # sameReturnFlag = send_same_user_list(sameUserList, userInfoDict, dbConn, mngApi)
    # if sameReturnFlag == False:
    #     print("##### 동명이인 정보 API 전송 실패")
    #     # 동명이인정보 전송이 실패하더라도 검증된 회원의 정보전송은 실행할 수 있도록 정상리턴처리
    #     return resultUserList
    #
    return resultUserList

def add_confirm_user(userInfoList, gui_root):
    """
    최종연계회원정보 + 동명이인 판별완료 회원정보 추가
    :param userInfoList: 최종연계회원정보 List
    :param gui_root: GUI Object
    :return: 최종연계회원정보(동명이인 판별완료 회원정보 추가된)
    """
    try:
        # API 로 동명이인 판별완료 회원정보 요청
        mngApi = connApi.api_manager()  # API 전송을 위한 커넥션 생성
        apiParam = dict()
        apiParam['PHARMACY_IDX'] = userInfoDict['PharmacyIdx']

        params = json.dumps(apiParam)
        url = iniDrxsDict['apiurl'] + '/getMemberPharmacySameNameChoice_v1.drx'

        returnKey, returnValuse = mngApi.api_conn_post(url, params)
        # print("#####(add_confirm_user-returnKey) :: ", returnKey)
        # print("#####(add_confirm_user-returnValuse) :: ", returnValuse)

        if type(returnValuse) != dict:
            logger_file.log_error("getMemberPharmacySameNameChoice_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
            return False

    except Exception as e:
        print("##### (add_confirm_user) error :: ", e)
    else:
        if returnValuse['STATUS'] == 'ok':
            if returnValuse['DATA_COUNT'] > 0:
                # 최종연계대상정보 + 동명이인 판별 완료 정보
                # print("##### (add_confirm_user) - userInfoList :: ", userInfoList)
                for userInfo in returnValuse['ITEMS']:
                    # print("##### (add_confirm_user) - userInfo :: ", userInfo)
                    tempDict1 = dict()
                    tempDict1['CusNo'] = userInfo['CHRTNO']
                    tempDict1['FamNo'] = userInfo['FAM_NM']
                    tempDict1['CusNm'] = userInfo['PAT_NM']
                    tempDict1['CusJmno'] = ''
                    tempDict1['RealBirth'] = ''
                    tempDict1['Sex'] = ''
                    tempDict1['UserId'] = ''
                    tempDict1['UserName'] = userInfo['PAT_NM']
                    tempDict1['Mobile'] = ''
                    tempDict1['birth'] = ''
                    tempDict1['regi_date'] = ''

                    tempDict = {
                        'CusNo': {
                            0 : userInfo['CHRTNO']
                        },
                        'FamNo': {
                            0: userInfo['CHRTNO']
                        },
                        'CusNm': {
                            0: userInfo['PAT_NM']
                        },
                        'CusJmno': {
                            0: ''
                        },
                        'RealBirth': {
                            0: ''
                        },
                        'Sex': {
                            0: ''
                        },
                        'HpTel': {
                            0: ''
                        },
                        'CertiNo': {
                            0: userInfo['INS_NUMBER']
                        },
                    }

                    # print("##### (add_confirm_user) - tempDict1 :: ", tempDict1)
                    # print("##### (add_confirm_user) - tempDict :: ", tempDict)
                    userInfoListGlobal.append(tempDict1)
                    userInfoList.append(tempDict)

        return userInfoList

##########################################################################################
####### 전송부 (위드팜)
##########################################################################################

def response_server_part(userInfoList, gui_root):
    """
    내손안의약국 서버로 처방전/청구가격정보/약정보를 조회 및 API 전송
    :param userInfoList: 처방전 전달할 최종 유저 리스트
    :param gui_root: GUI 객체
    :return: T/F
    """
    print("##### (전송부) 연계대상의 처방전 전송부 프로세스를 수행합니다.")
    if len(userInfoListGlobal) > 0:
        gui_root.textInsert("최종연계대상의 처방전 정보를 연계하는 프로세스를 시작합니다.")
        # logger_file.log_info("### 최종 조제내역연계대상의 조제내역을 연계합니다.")
    else:
        gui_root.textInsert("최종연계대상이 존재하지않습니다.")
        logger_file.log_info("### 최종 조제내역 연계대상이 존재하지않습니다.")
        # logger_file.log_info("##################################################################")

    common = commonCode.commonCode()
    mngApi = connApi.api_manager()  # API 전송을 위한 커넥션 생성
    dbConn = connDb.Manage_logcal_db(iniDatabaseDict['server'], iniDatabaseDict['database'],iniDatabaseDict['username'], iniDatabaseDict['password'], iniDatabaseDict['conntime'] if 'conntime' in iniDatabaseDict else 1800)
    # dbConn = connDb.Manage_logcal_db('localhost\tood2008', 'WithpharmErp', 'sa', '$dnlemvka3300$32!')
    # 연계 유저별 루프 (기존 연계방식)
    # print("##### userInfoListGlobal :: ", userInfoListGlobal)

    for userInfo in userInfoListGlobal:
        ################################################
        # 1. 유저의 처방전 정보 조회 & 처방전 전송
        # gui_root.textInsert(str(""))
        print("#### 최종연계대상 정보 userInfo :: ", userInfo)
        userInfo['PharmacyIdx'] = str(PharmIdx)     # 유저정보에 약국의 IDX 코드를 삽입
        # logger_file.log_info("### {} 회원의 조제내역을 연계합니다.".format(str(userInfo['UserName'])))

        # TODO 타인처방전 전송에 필요(현위치에서는 본인처방전 전송AUTH1이므로 0고정)
        # TODO 230830 본인처방일때는 본인 UserId(MemberIdx)를 추가하여 처리한다, ID가 있을경우 해당유저의 데이터로 조제내역을 만드므로
        userInfo['OtherUserId'] = str(userInfo['UserId'])

        gui_root.textInsert(str(userInfo['CusNm']+" 사용자의 처방전 정보를 조회합니다."))
        queryArr = []
        queryArr.append("SELECT")
        queryArr.append("A.PrescriptionCd, A.CusNo, A.InsuGb, A.CareGb, A.InsuEtc, A.SendGb, A.RootCusNm, A.PromissNo, A.InsuNo, A.CusNm, A.CusJmno, A.HospitalNo, A.Doctor, A.DoctorSeq")
        queryArr.append(", CONVERT(VARCHAR, A.MakeDte, 23) AS MakeDte, A.PregYn, A.MakeDay, A.ConDay, CONVERT(VARCHAR, A.PresDte, 23) AS PresDte, A.PresNo, A.UseDay, A.DisCd1, A.DisCd2, A.SpecialCd, A.LicenseNo, A.BabyYn, A.OverTime, A.UserTime, A.StateGb")
        queryArr.append(", A.CareHospitalGb, CONVERT(VARCHAR, A.RDte, 120) AS RDte, A.RUser, CONVERT(VARCHAR, A.MDte, 120) AS MDte, A.MUser, CONVERT(VARCHAR, A.CDte, 120) AS CDte, A.CUser, A.DelYn, A.ErrGb, A.LabelYn, A.PrescriptionSeq, A.PosPayGb, A.NimsGb, A.PowderYn, B.TransStatus, B.TransDt")
        queryArr.append(",ISNULL((SELECT MedicalNm FROM [WithpharmErp].[dbo].[InfoMedical] WHERE 1=1 AND MedicalNo = A.HospitalNo), '') AS HospitalNm")
        queryArr.append(",ISNULL((SELECT MedicalTel FROM [WithpharmErp].[dbo].[InfoMedical] WHERE 1=1 AND MedicalNo = A.HospitalNo), '') AS HospitalTel")
        queryArr.append(",ISNULL((SELECT QrcodeIdx FROM WithpharmDrx.dbo.DrxQr1 WHERE 1=1 AND PrescriptionCd = A.PrescriptionCd), '') AS QrcodeIdx")
        queryArr.append("FROM WithpharmErp.dbo.Prescription AS A WITH(NOLOCK)")
        queryArr.append("LEFT OUTER JOIN WithpharmDrx.dbo.DrxsPrescriptionLinkInfo AS B")
        queryArr.append("ON A.PrescriptionCd = B.PrescriptionCd")

        # TODO 230818 AUTH2의 전송해야할 PrescriptionCd는 제외하도록 변경
        queryArr.append("LEFT OUTER JOIN WithpharmDrx.dbo.DrxsCustomersAuth2 AS A2")
        queryArr.append("ON A.PrescriptionCd = A2.PrescriptionCd AND A2.DelFlag = 'N'")

        queryArr.append("WHERE A.CusNo = '"+userInfo['CusNo']+"'")
        queryArr.append("AND A.StateGb <> '1'")         # 조제준비중 상태가 아닌 데이터
        queryArr.append("AND A.DelYn = 'N'")            # 삭제 처리 되지않은 데이터
        # TODO 여기 아래 날자 바꿔야함. (내부 협의 후 날자 선정 필요함), 연계회원(약국)이 내손안의약국에 가입한 날자를 기준으로 하면 좋을듯
        # TODO 230309 : 오늘 기준 1년전까지의 데이터중 검색하는것으로 바꿔도 좋을듯... 현재는 ini에 등록된 기준일자 기준...
        # queryArr.append("AND A.PresDte BETWEEN CONVERT(DATE, '"+iniDrxsDict['linkdate']+"') AND CONVERT(CHAR(10), GETDATE(), 23)")   # 날자를 해당 회원이 내손안의약국에 연계 동의한 날자로 바꿔줘야함
        queryArr.append("AND CONVERT(CHAR(10), A.PresDte, 23) BETWEEN CONVERT(CHAR(10), DATEADD(YEAR, -1, GETDATE()), 23) AND CONVERT(CHAR(10), GETDATE(), 23)")    # 오늘기준 1년전 데이터까지 조회
        queryArr.append("AND B.PrescriptionCd IS NULL")   # 전송완료 테이블에 존재하는 처방전 데이터는 재전송하지않기 위해 제외
        queryArr.append("AND A2.PrescriptionCd IS NULL")  # TODO 230818 AUTH2 조제내역은 제외 (별도전송하므로)
        queryStr = " ".join(queryArr)

        dbConn.conn_open()
        queryResultPrescription = dbConn.send_query(queryStr)
        dbConn.conn_close()

        # False 가 리턴될 경우 쿼리 except에서 False 처리 한 것이므로 리턴처리하고 다음 사이클로 넘긴다
        if type(queryResultPrescription) == bool and not queryResultPrescription:
            return False

        if type(queryResultPrescription) != pd.DataFrame:
            return False

        if type(queryResultPrescription) == pd.DataFrame and queryResultPrescription.empty:
            # print("##### ("+userInfo['CusNm']+") 해당 연계회원은 처방전 내역이 존재하지않습니다.")
            gui_root.textInsert(str(userInfo['CusNm'] + " 님의 연계할 처방전 정보가 현재 존재하지않습니다."))
            continue
        # else:
        #     logger_file.log_info("### {} 회원의 신규조제내역 {} 건을 전송처리합니다.".format(str(userInfo['CusNm']), len(queryResultPrescription)))

        # print("##### 연계회원 (" + userInfo['CusNm'] + ") 님 처방전 조회 결과 #####")
        # print(queryResultPrescription)
        print("## 조제내역 sql 검색 결과 :: {}".format(queryResultPrescription))
        print("## 대상 조제정보 조회 쿼리 타입 :: {}".format(type(queryResultPrescription)))

        splitCount = 3  # 처방전 분할 기준 갯수
        # print("##### 분할전송 처방전 전체갯수 :: ", len(queryResultPrescription))
        for rowIndex in range(0, len(queryResultPrescription), splitCount):  # splitCount 갯수만큼 분할하여 처리
            # print("##### splitCount :: ", splitCount)
            # print("##### rowIndex :: ", rowIndex)
            # print("##### len(queryResultPrescription) :: ", len(queryResultPrescription))
            # print("##### len(queryResultPrescription)-rowIndex :: ", len(queryResultPrescription)-rowIndex)
            tempDataframe = queryResultPrescription.iloc[rowIndex:rowIndex + splitCount]  # 처방전 데이터 프레임 생성

            if (len(queryResultPrescription)-rowIndex) < splitCount:    # splitCount 갯수보다 남은게 작을 경우 (마지막 회차)
                # print("##### ("+userInfo['CusNm']+") 분할전송 마지막 회차 전송")
                # print("##### len(tempDataframe) :: ", len(tempDataframe))
                # print("##### tempDataframe :: ", tempDataframe)
                gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 처방전 정보를 전송합니다."))
                # logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 처방전 정보를 전송합니다."))
                print("## send_prescription param :: {} ::: {}".format(tempDataframe, userInfo))
                send_prescription(tempDataframe, userInfo, dbConn, mngApi)  # 처방전 데이터프레임 API 전송

                for index, row in tempDataframe.iterrows():
                    gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 처방전 청구정보를 전송합니다."))
                    # logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 처방전 청구정보를 전송합니다."))
                    resultFlag = send_prescription_amt(row, userInfo, dbConn, mngApi)  # 처방전 청구정보 조회 및 API 전송
                    if resultFlag:
                        gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 처방전 약정보를 전송합니다."))
                        # logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 처방전 약정보를 전송합니다."))
                        resultFlag = send_prescription_drug(row, userInfo, dbConn, mngApi)  # 처방전 약정보 조회 및 API 전송
                        if resultFlag:
                            gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리를 진행합니다."))
                            # logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리를 진행합니다."))
                            resultFlag = insert_prescription_send_flag(row, userInfo, dbConn, '1')  # 처방전 전송완료 처리(로컬DB)
                            if not resultFlag:
                                gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리중 오류가발생하였습니다."))
                                logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리중 오류가발생하였습니다."))
                                print("##### 처방전 전송완료 로컬플래그처리 실패!!!")
                        else:
                            gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 약정보 전송처리중 오류가발생하였습니다."))
                            logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 약정보 전송처리중 오류가발생하였습니다."))
                            print("##### 처방전 약정보 전송 실패!!!")
                    else:
                        gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 청구정보 전송처리중 오류가발생하였습니다."))
                        logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 청구정보 전송처리중 오류가발생하였습니다."))
                        print("##### 처방전 청구정보 전송 실패!!!")

            else:
                # (분할전송) 처방전 정보
                # print("##### (" + userInfo['CusNm'] + ") 분할한 tempDataframe 타입 :: ", type(tempDataframe))
                # print("##### (" + userInfo['CusNm'] + ") 분할한 tempDataframe 데이터 :: ", tempDataframe)

                gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 정보를 전송합니다."))
                # logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 정보를 전송합니다."))
                send_prescription(tempDataframe, userInfo, dbConn, mngApi)      # 처방전 데이터프레임 API 전송

                # (분할전송) 처방전 청구정보 및 처방전 약정보
                for index, row in tempDataframe.iterrows():
                    gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 청구정보를 전송합니다."))
                    # logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 청구정보를 전송합니다."))
                    resultFlag = send_prescription_amt(row, userInfo, dbConn, mngApi)        # 처방전 청구정보 조회 및 API 전송
                    if resultFlag:
                        gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 약정보를 전송합니다."))
                        # logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 약정보를 전송합니다."))
                        resultFlag = send_prescription_drug(row, userInfo, dbConn, mngApi)       # 처방전 약정보 조회 및 API 전송
                        if resultFlag:
                            gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리를 진행합니다."))
                            # logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리를 진행합니다."))
                            resultFlag = insert_prescription_send_flag(row, userInfo, dbConn, '1')  # 처방전 전송완료 처리(로컬DB)
                            if not resultFlag:
                                gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리중 오류가발생하였습니다."))
                                logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리중 오류가발생하였습니다."))
                                print("##### 처방전 전송완료 로컬플래그처리 실패!!!")
                        else:
                            gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 약정보전송처리중 오류가발생하였습니다."))
                            logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 약정보전송처리중 오류가발생하였습니다."))
                            print("##### 처방전 약정보 전송 실패!!!")
                    else:
                        gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 청구정보 전송처리중 오류가발생하였습니다."))
                        logger_file.log_info(str(userInfo['CusNm'] + " 사용자의 대상 처방전 청구정보 전송처리중 오류가발생하였습니다."))
                        print("##### 처방전 청구정보 전송 실패!!!")

    userInfoListGlobal.clear()

    # 연계 유저별 루프 (픽업서비스 조제데이터 전달)
    # TODO 230330 AUTH2의 연계해야할 정보를 조회?하여 회원정보 입력? 연계해야할 정보 조회 연계로그테이블과 조인필요
    """
    1. 전송이력과 비교조회하여 전송해야할 데이터와 데이터 내 CusNo를 통해 회원정보 조회
        이정보들도 추가로 필요함
        jsonStr['PharmacyIdx'] = userInfo['PharmacyIdx']
        jsonStr['CusNo'] = userInfo['CusNo']
        jsonStr['UserId'] = userInfo['UserId']
        jsonStr['CusNm'] = userInfo['CusNm']
        jsonStr['RealBirth'] = userInfo['RealBirth']
        jsonStr['CusJmno'] = userInfo['CusJmno']
    2. 쿼리한개로 조회 후 위 정보는 별도로 dict로 만들어둔다 (전송 메서드 인자로 활용) 
    """
    # 연계 대상 기준 데이터 조회
    auth2_send_user_list = []
    auth2_send_user_list.append("SELECT A2.QrNm, A2.CusNo, A2.QrcodeIdx, A2.PrescriptionCd, A2.DelFlag, CONVERT(VARCHAR, A2.DelFlagModDt, 120) AS DelFlagDt, A2.UserId, PC.CusNm, PC.CusJmno, PC.RealBirth")
    # TODO 230818 : 타인처방전 환자의 내손안의약국 회원여부를 확인하기 위한 추가 조회 필요
    auth2_send_user_list.append(", (SELECT PP.CusNo FROM WithpharmErp.dbo.Prescription AS PP WHERE 1=1 AND PP.PrescriptionCd = A2.PrescriptionCd) AS P_CUS_NO")
    auth2_send_user_list.append(", ISNULL((SELECT UserId FROM WithpharmDrx.dbo.DrxsCustomersAuth AS A1 WHERE 1=1 AND A1.CusNo = A2.CusNo), 0) AS P_USER_ID")
    auth2_send_user_list.append("FROM WithpharmDrx.dbo.DrxsCustomersAuth2 AS A2")
    auth2_send_user_list.append("INNER JOIN WithpharmErp.dbo.PatientCustomers AS PC")
    auth2_send_user_list.append("ON A2.CusNo = PC.CusNo")
    auth2_send_user_list.append("LEFT OUTER JOIN (SELECT CusNo, UserId, PrescriptionCd FROM WithpharmDrx.dbo.DrxsPrescriptionLinkInfo WHERE 1=1 AND TransStatus = 'Y') AS DP")
    auth2_send_user_list.append("ON A2.PrescriptionCd = DP.PrescriptionCd AND A2.UserId = DP.UserId")
    auth2_send_user_list.append("WHERE 1=1")
    auth2_send_user_list.append("AND A2.DelFlag = 'N'")
    auth2_send_user_list.append("AND DP.PrescriptionCd IS NULL")

    # auth2_send_user_list.append("SELECT A2.QrNm, A2.CusNo, A2.QrcodeIdx, A2.PrescriptionCd, A2.DelFlag, CONVERT(VARCHAR, A2.DelFlagModDt, 120) AS DelFlagDt, A2.UserId, PC.CusNm, PC.CusJmno, PC.RealBirth")
    # auth2_send_user_list.append("FROM WithpharmDrx.dbo.DrxsCustomersAuth2 AS A2")
    # auth2_send_user_list.append("LEFT OUTER JOIN (SELECT CusNo, PrescriptionCd FROM WithpharmDrx.dbo.DrxsPrescriptionLinkInfo WHERE 1=1 AND TransStatus = 'Y') AS DP")
    # auth2_send_user_list.append("ON A2.PrescriptionCd = DP.PrescriptionCd AND A2.CusNo = DP.CusNo")
    # auth2_send_user_list.append("INNER JOIN WithpharmErp.dbo.PatientCustomers AS PC")
    # auth2_send_user_list.append("ON A2.CusNo = PC.CusNo")
    # auth2_send_user_list.append("WHERE 1=1")
    # auth2_send_user_list.append("AND A2.DelFlag = 'N'")
    # auth2_send_user_list.append("AND DP.PrescriptionCd IS NULL")
    auth2_send_user_query = " ".join(auth2_send_user_list)

    dbConn.conn_open()
    auth2_send_user_result = dbConn.send_query(auth2_send_user_query)
    dbConn.conn_close()

    if type(auth2_send_user_result) == bool and not auth2_send_user_result:
        return False

    if type(auth2_send_user_result) != bool and auth2_send_user_result.empty:
        print("AUTH2 연계대상 정보가 존재하지않습니다.")
        logger_file.log_info("### 타인 픽업처방전 조제내역 연계 대상이 존재하지않습니다.")
    else:
        auth2_send_user_result_dict = auth2_send_user_result.to_dict()
        print("## auth2_send_user_result_dict :: {}".format(auth2_send_user_result_dict))

        # logger_file.log_info("### 타인 픽업처방전 조제내역을 전송합니다.")
        if len(auth2_send_user_result_dict['PrescriptionCd']) > 0:
            for idx in range(0, len(auth2_send_user_result_dict['PrescriptionCd'])):
                # 회원정보 dict 생성
                auth2_user_dict = dict()
                auth2_user_dict['PharmacyIdx'] = userInfoDict['PharmacyIdx']
                # TODO 231215 이거 CusNo가 P_Cus_No 가 되어야하는거 아닌가?
                # TODO 231215 A2.CusNo는 AUTH2 이므로 이게 맞는데 왜 임상헌 단골의 정보가 아닌 임성수(미단골-타인)의 조제내역이 연계된거지?
                auth2_user_dict['CusNo'] = auth2_send_user_result_dict['CusNo'][idx]
                # TODO 231215 여기 UserId는 AUTH2의 UserId
                auth2_user_dict['UserId'] = auth2_send_user_result_dict['UserId'][idx]
                auth2_user_dict['CusNm'] = auth2_send_user_result_dict['CusNm'][idx]
                auth2_user_dict['RealBirth'] = auth2_send_user_result_dict['RealBirth'][idx]
                auth2_user_dict['CusJmno'] = auth2_send_user_result_dict['CusJmno'][idx]
                # TODO 231215 밑 P_USER_ID가 AUTH에 있는 USER_ID
                auth2_user_dict['OtherUserId'] = str(auth2_send_user_result_dict['P_USER_ID'][idx])  # TODO 230818 : 타인처방전환자정보의 UserId(회원일경우IDX, 회원아닐경우0)

                print("### (AUTH2 연계대상회원정보) auth2_user_dict :: {}".format(auth2_user_dict))

                # 연계 대상 회원별 조제내역 단건 조회
                auth2_send_query_list = []
                auth2_send_query_list.append("SELECT A.PrescriptionCd, A.CusNo, A.InsuGb, A.CareGb, A.InsuEtc, A.SendGb, A.RootCusNm, A.PromissNo, A.InsuNo, A.CusNm, A.CusJmno, A.HospitalNo, A.Doctor, A.DoctorSeq")
                auth2_send_query_list.append(", CONVERT(VARCHAR, A.MakeDte, 23) AS MakeDte, A.PregYn, A.MakeDay, A.ConDay, CONVERT(VARCHAR, A.PresDte, 23) AS PresDte, A.PresNo, A.UseDay, A.DisCd1, A.DisCd2, A.SpecialCd, A.LicenseNo, A.BabyYn, A.OverTime, A.UserTime, A.StateGb")
                auth2_send_query_list.append(", A.CareHospitalGb, CONVERT(VARCHAR, A.RDte, 120) AS RDte, A.RUser, CONVERT(VARCHAR, A.MDte, 120) AS MDte, A.MUser, CONVERT(VARCHAR, A.CDte, 120) AS CDte, A.CUser, A.DelYn, A.ErrGb, A.LabelYn, A.PrescriptionSeq, A.PosPayGb, A.NimsGb, A.PowderYn")
                auth2_send_query_list.append(", ISNULL((SELECT MedicalNm FROM WithpharmErp.dbo.InfoMedical WHERE 1=1 AND MedicalNo = A.HospitalNo), '') AS HospitalNm")
                auth2_send_query_list.append(", ISNULL((SELECT MedicalTel FROM WithpharmErp.dbo.InfoMedical WHERE 1=1 AND MedicalNo = A.HospitalNo), '') AS HospitalTel")
                # auth2_send_query_list.append(", '' AS QrcodeIdx")
                auth2_send_query_list.append(", ISNULL((SELECT QrcodeIdx FROM WithpharmDrx.dbo.DrxQr1 WHERE 1=1 AND PrescriptionCd = A.PrescriptionCd), '') AS QrcodeIdx")
                auth2_send_query_list.append("FROM WithpharmErp.dbo.Prescription AS A WITH(NOLOCK)")
                # auth2_send_query_list.append("INNER JOIN WithpharmDrx.dbo.DrxsCustomersAuth2 AS A2")
                # auth2_send_query_list.append("ON A.PrescriptionCd = A2.PrescriptionCd AND A.CusNo = A2.CusNo")
                # auth2_send_query_list.append("LEFT OUTER JOIN WithpharmDrx.dbo.DrxsPrescriptionLinkInfo AS B")
                # auth2_send_query_list.append("ON A.PrescriptionCd = B.PrescriptionCd")
                auth2_send_query_list.append("WHERE 1=1")
                # auth2_send_query_list.append("AND CONVERT(CHAR(10), RDte, 23) BETWEEN CONVERT(CHAR(10), DATEADD(YEAR, -1, GETDATE()), 23) AND CONVERT(CHAR(10), GETDATE(), 23)")
                auth2_send_query_list.append("AND A.PrescriptionCd = '" + auth2_send_user_result_dict['PrescriptionCd'][idx] + "'")
                auth2_send_query_list.append("AND A.StateGb <> '1'")
                auth2_send_query_list.append("AND A.DelYn = 'N'")
                # auth2_send_query_list.append("AND B.PrescriptionCd IS NULL")
                auth2_send_query = " ".join(auth2_send_query_list)

                dbConn.conn_open()
                auth2_send_query_result = dbConn.send_query(auth2_send_query)
                dbConn.conn_close()

                if type(auth2_send_query_result) == bool and not auth2_send_query_result:
                    return False

                if type(auth2_send_query_result) != bool and auth2_send_query_result.empty:
                    print("## (AUTH2 전송) 처방전 데이터가 존재하지 않습니다.")
                else:
                    print("## (AUTH2-전송) AUTH2 타인처방전 정보를 API 전송합니다")
                    logger_file.log_info("### {} 회원의 타인처방전 조제내역 {} 건을 전송처리합니다.".format(str(auth2_user_dict['CusNm']), len(auth2_send_query_result)))
                    # logger_file.log_info("### {} 회원의 타인처방전 조제내역을 전송합니다".format(str(auth2_user_dict['CusNm'])))
                    send_prescription(auth2_send_query_result, auth2_user_dict, dbConn, mngApi)  # 처방전 데이터프레임 API 전송

                    for index, row in auth2_send_query_result.iterrows():
                        print("## (AUTH2-전송) AUTH2 타인처방전 청구정보를 API 전송합니다")
                        # logger_file.log_info("### {} 회원의 타인처방전 청구정보를 API 전송합니다".format(str(auth2_user_dict['CusNm'])))
                        result_flag_amt = send_prescription_amt(row, auth2_user_dict, dbConn, mngApi)  # 처방전 청구정보 조회 및 API 전송
                        if result_flag_amt:
                            print("## (AUTH2-전송) AUTH2 타인처방전 약정보를 API 전송합니다")
                            # logger_file.log_info("### {} 회원의 타인처방전 약정보를 API 전송합니다".format(str(auth2_user_dict['CusNm'])))
                            result_flag_drug = send_prescription_drug(row, auth2_user_dict, dbConn, mngApi)  # 처방전 약정보 조회 및 API 전송
                            if result_flag_drug:
                                print("## (AUTH2-전송) AUTH2 타인처방전 전송이력 정보를 DB 등록합니다.")
                                logger_file.log_info("### {} 회원의 타인처방전 전송이력 정보를 DB 등록합니다.".format(str(auth2_user_dict['CusNm'])))
                                result_flag_status = insert_prescription_send_flag(row, auth2_user_dict, dbConn, '2')  # 처방전 전송완료 처리(로컬DB)
                                if not result_flag_status:
                                    print("(AUTH2) 처방전 전송완료 전송정보등록실패")
                                    logger_file.log_info("### {} 회원의 타인처방전 전송완료 전송정보등록실패".format(str(auth2_user_dict['CusNm'])))
                            else:
                                print("(AUTH2) 처방전 약정보 전송실패")
                                logger_file.log_info("### {} 회원의 타인처방전 약정보 전송실패".format(str(auth2_user_dict['CusNm'])))
                        else:
                            print("(AUTH2) 처방전 청구정보 전송실패")
                            logger_file.log_info("### {} 회원의 타인처방전 청구정보 전송실패".format(str(auth2_user_dict['CusNm'])))



##########################################################################################
####### 처방전(내역,가격,약물)정보 조회 및 API 전송 (위드팜)
##########################################################################################

def send_same_user_list(sameuserList, pharmacyInfo, dbConn, mngApi):
    """
    동명이인 정보를 API 전송한다.
    :param sameuserList: 동명이인 정보
    :param pharmacyInfo: 약국정보
    :param dbConn: DB Connection
    :param mngApi: API 객체
    :return:
    """
    try:
        # print("##### (동명이인정보 전송) 동명이인정보 전송을 수행합니다. ")
        common = commonCode.commonCode()
        returnJsonData = common.packageJsonSameUserInfo(sameuserList, pharmacyInfo)

        if returnJsonData == '':
            return False

        # print("전송할 동명이인 정보 :: ", returnJsonData)
    except Exception as e:
        print("(send_same_user_list) error :: ", e)
    else:
        checkUrl = iniDrxsDict['apiurl'] + '/setMemberPharmacySameName_v1.drx'  # 동명이인정보전송API 주소
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrl, returnJsonData)  # 동명이인정보전송

        if type(apiResultDatas) != dict:
            logger_file.log_error("setMemberPharmacySameName_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
            return False

        # print("동명이인API 전송 결과 :: ")
        # print(apiResultKey)
        # print(apiResultDatas)

        if apiResultDatas['Status'] == 'ok':
            return True
        else:
            return False

def send_prescription_mapping(dataFrame, pharmacy_idx, mngApi):
    """
    전송된 조제내역중 삭제된 조제내역을 API 전송한다.
    :param dataFrame:
    :param pharmacy_idx:
    :return:
    """
    try:
        head_dict = dict()
        head_dict['pharmacy-idx'] = pharmacy_idx

        doby_list = []
        for idx in range(0, len(dataFrame['PrescriptionCd'])):
            body_dict = dict()
            body_dict['user-id'] = str(dataFrame['PrescriptionCd'][idx])
            body_dict['prescription-cd'] = str(dataFrame['PrescriptionCd'][idx])
            body_dict['modify-date'] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            doby_list.append(body_dict)

        head_dict['items'] = doby_list
        transJsonStr = json.dumps(head_dict)

        print("## 삭제처리된 조제내역 전송 JSON ::: {}".format(transJsonStr))
        # https://dev-wp-api.drxsolution.co.kr/setMemberBillingSoftwareSyncData.drx
        checkUrl = iniDrxsDict['apiurl'] + '/setMemberBillingSoftwareSyncData_v1.drx'  # 전송 내역 중 삭제된 처방전 정보 전송 API
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrl, transJsonStr)  # 처방전 POST 방식 전송

        if type(apiResultDatas) != dict:
            logger_file.log_error("setMemberBillingSoftwareSyncData_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
            return False

    except BaseException as e:
        print(traceback.format_exc())
        return False
    else:
        return True

def send_prescription(dataFrame, userInfo, dbConn, mngApi):
    """
    처방전 정보를 API 전송한다.
    :param dataFrame:
    :param userInfo:
    :param dbConn:
    :param mngApi:
    :return:
    """
    print("##### (처방전 전송) 처방전 전송을 수행합니다. ")
    print("##### ("+userInfo['CusNm']+") 연계회원의 처방전을 전송합니다.")
    try:
        common = commonCode.commonCode()
        transJsonStr = common.packageJsonPrescription(dataFrame, userInfo)  # 처방전 데이터를 JSON 화
        checkUrl = iniDrxsDict['apiurl'] + '/userPrescription_v1.drx'  # 처방전 전송 API URL
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrl, transJsonStr)  # 처방전 POST 방식 전송

        if type(apiResultDatas) != dict:
            logger_file.log_error("userPrescription_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
            return False

        # 오류처리
        if type(apiResultKey) == bool and not apiResultKey:
            logger_file.log_error("## (userPrescription.drx) API ERROR :: {}".format(apiResultDatas))
            logger_api.send_api_log('', '', userInfo['PharmacyIdx'], 'ERR-201', '(userPrescription.drx) API SEND ERROR')
            return False

    except BaseException as e:
        print("##### (send_prescription) Error :: ", e)
        logger_file.log_error("(userPrescription.drx) API ERROR :: {}".format(traceback.format_exc()))

        # API 발송 오류일 경우
        if type(apiResultKey) == bool and not apiResultKey:
            logger_file.log_error("## (userPrescription.drx) API ERROR :: {}".format(apiResultDatas))
            logger_api.send_api_log('', '', userInfo['PharmacyIdx'],'ERR-201', '(userPrescription.drx) API SEND ERROR')
        return False
    else:
        return True
        
def send_prescription_amt(dataFrame, userInfo, dbConn, mngApi):
    """
    처방전 가격정보 로컬DB조회 및 API 전송
    :param dataFrame: 처방전 데이터 프레임
    :param userInfo: 대상 유저정보
    :param dbConn: DB 커넥션
    :param mngApi: API 커넥션
    :return: T/F
    """
    print("##### (처방전 청구정보전송) 처방전 청구가격정보 전송을 수행합니다. ")
    print("##### (" + userInfo['CusNm'] + ") 연계회원의 처방전 청구가격정보를 전송합니다.")
    # print("##### (처방전 청구정보전송) dataFrame {}".format(dataFrame))
    # print("##### (처방전 청구정보전송) userInfo {}".format(userInfo))

    try:
        common = commonCode.commonCode()
        # 처방전 청구가격정보 쿼리
        # print("##### (청구가격정보) dataFrame :: ", dataFrame)
        # print("##### (청구가격정보) type(dataFrame) :: ", type(dataFrame))

        # print("##### 처방전 고유번호 (" + dataFrame['PrescriptionCd'] + ")")
        queryArr = []
        queryArr.append("SELECT")
        queryArr.append("PrescriptionCd , tAmt1, sAmt, BillAmt, SupportAmt, tAmt2, mBillAmt, DrugDiffAmt, TotAmt, t100Amt, mAmt, t100mAmt, s100mAmt")
        queryArr.append(", Bill100mtAmt, Bill100mmAmt, Rate, TotalSelfAmt, mTotBAmt, mBillBAmt, TotalAmt, BExcept")
        queryArr.append("FROM WithpharmErp.dbo.PrescriptionAmt")
        # 인자값 바꿔줘야함 제일처음 처방전 쿼리결과에서..
        queryArr.append("WHERE PrescriptionCd = '" + dataFrame['PrescriptionCd'] + "'")
        print("(send_prescription_amt) queryArr :: {}".format(queryArr))
        queryStr = " ".join(queryArr)

        dbConn.conn_open()
        queryResultAmt = dbConn.send_query(queryStr)
        dbConn.conn_close()

        if type(queryResultAmt) == bool and not queryResultAmt:
            return False

        # print("##### (" + userInfo['CusNm'] + ") 처방전 가격정보 ")
        # print(queryResultAmt)

        # if len(queryResultAmt) == 0:  # 처방전 청구정보 존재여부확인
        #     print("##### (" + userInfo['CusNm'] + ")님의 처방전(" + dataFrame['PrescriptionCd'] + ")청구가격정보가 존재하지않습니다.")

        print("## packageJsonPrescriptionAmt param :: {} ::: {}".format(queryResultAmt, userInfo))

        transJsonStrAmt = common.packageJsonPrescriptionAmt(queryResultAmt, userInfo)
        # print("##### (처방전 청구정보전송-분할) transJsonStrAmt :: ", transJsonStrAmt)

        checkUrlAmt = iniDrxsDict['apiurl'] + '/userPrescriptionAmt_v1.drx'
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrlAmt, transJsonStrAmt)  # POST 방식 전송
        # print("##### (처방전-분할 청구정보) 일괄전송결과 apiResultKey :: ", apiResultKey)
        # print("##### (처방전-분할 청구정보) 일괄전송결과 apiResultDatas :: ", apiResultDatas)

        if type(apiResultDatas) != dict:
            logger_file.log_error("userPrescriptionAmt_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
            return False

    except Exception as e:
        print("##### (userPrescriptionAmt.drx) Error :: ", e)
        logger_file.log_error("(userPrescriptionAmt.drx) API ERROR :: {}".format(traceback.format_exc()))

        # API 발송 오류일 경우
        if type(apiResultKey) == bool and not apiResultDatas:
            logger_file.log_error("## (userPrescriptionAmt.drx) API ERROR :: {}".format(apiResultDatas))
            logger_api.send_api_log('', '', userInfo['PharmacyIdx'], 'ERR-201', '(userPrescriptionAmt.drx) API SEND ERROR')

        return False
    else:
        return True

def send_prescription_drug(dataFrame, userInfo, dbConn, mngApi):
    """
    처방전 약정보 로컬DB조회 및 API 전송
    :param dataFrame: 처방전 데이터 프레임
    :param userInfo: 대상 유저정보
    :param dbConn: DB 커넥션
    :param mngApi: API 커넥션
    :return: T/F
    """
    print("##### (처방전 약물정보 전송) 처방전 약물정보 전송을 수행합니다. ")
    print("##### (" + userInfo['CusNm'] + ") 연계회원의 처방전 약물정보를 전송합니다.")

    try:
        common = commonCode.commonCode()
        # print("##### (약정보) dataFrame :: ", dataFrame)
        # print("##### (약정보) type(dataFrame) :: ", type(dataFrame))

        # print("##### 처방전 고유번호 (" + dataFrame['PrescriptionCd'] + ")")
        # 처방약 데이터 조회 TODO 230110 처방약 + 조제약(대체약) 조회 변경
        # queryArr = []
        # queryArr.append("SELECT")
        # queryArr.append(
        #     "a.PrescriptionCd , a.Seq, a.Gb, a.ItemType, a.ItemCd, a.Price, a.EatDay, a.TotDay, a.EatOnce, a.TotQty, a.Amt, a.MaxAmt, a.DrugDiffAmt")
        # queryArr.append(", MakeGb, EatGb, PasYn, LinkLabel, ItemSeq")
        # queryArr.append(", ISNULL((SELECT EatNm FROM dbo.InfoDrugEat WHERE EatCd = a.EatGb), '') AS EatComment")
        # queryArr.append("FROM WithpharmErp.dbo.PrescriptionDrug AS a")
        # queryArr.append("WHERE PrescriptionCd = '" + dataFrame['PrescriptionCd'] + "'")
        # queryStr = " ".join(queryArr)
        #
        # dbConn.conn_open()
        # queryResultDrug = dbConn.send_query(queryStr)
        # dbConn.conn_close()

        # 조제약 데이터 조회
        queryArr = []
        queryArr.append("SELECT")
        queryArr.append("a.PrescriptionCd , a.Seq, a.Gb, a.ItemType, a.ItemCd, a.Price, a.EatDay, a.TotDay, a.EatOnce, a.TotQty, a.Amt, a.MaxAmt, a.DrugDiffAmt")
        queryArr.append(", MakeGb, EatGb, PasYn, LinkLabel, ItemSeq")
        queryArr.append(", ISNULL((SELECT EatNm FROM dbo.InfoDrugEat WHERE EatCd = a.EatGb), '') AS EatComment")
        queryArr.append(", CASE WHEN a.Gb = 'W' THEN ISNULL((SELECT ItemNm FROM WithpharmErp.dbo.InfoItem WHERE ItemCd = a.ItemCd), '') ELSE '' END AS ItemName")
        queryArr.append(", ISNULL((SELECT EdiCd FROM dbo.InfoItem WHERE ItemCd = a.ItemCd), '') AS EdiCd")
        queryArr.append("FROM WithpharmErp.dbo.PrescriptionDrugMake AS a WITH(NOLOCK)")
        # 인자값 바꿔줘야함 제일처음 처방전 쿼리결과에서..
        queryArr.append("WHERE PrescriptionCd = '" + dataFrame['PrescriptionCd'] + "'")
        # 날자를 해당 회원이 내손안의약국에 연계 동의한 날자로 바꿔줘야함
        queryStr = " ".join(queryArr)

        dbConn.conn_open()
        queryResultDrug = dbConn.send_query(queryStr)
        dbConn.conn_close()

        if type(queryResultDrug) == bool and not queryResultDrug:
            return False

        # print("##### (" + userInfo['CusNm'] + ") 처방전 약물정보 ")
        # print(queryResultDrug)

        # if len(queryResultDrug) == 0:  # 처방전 청구정보 존재여부확인
        #     print("##### (" + userInfo['CusNm'] + ")님의 처방전(" + dataFrame['PrescriptionCd'] + ")약정보가 존재하지않습니다.")

        print("## packageJsonPrescriptionDrug param :: {} ::: {}".format(queryResultDrug, userInfo))
        transJsonStrDrug = common.packageJsonPrescriptionDrug(queryResultDrug, userInfo)
        # print("##### (처방전 약물정보전송-분할) transJsonStrDrug :: ", transJsonStrDrug)

        print("### 처방전 약정보 전송 :: ")
        checkUrlAmt = iniDrxsDict['apiurl'] + '/userPrescriptionDrugInfo_v1.drx'
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrlAmt, transJsonStrDrug)  # POST 방식 전송
        # print("##### (처방전-분할 약물정보) 일괄전송결과 apiResultKey :: ", apiResultKey)
        # print("##### (처방전-분할 약물정보) 일괄전송결과 apiResultDatas :: ", apiResultDatas)

        if type(apiResultDatas) != dict:
            logger_file.log_error("userPrescriptionDrugInfo_v1 API 결과정보가 딕셔너리형태가 아닌 데이터로 판별되어 리턴처리합니다.")
            return False

    except Exception as e:
        print("##### (send_prescription_drug) Error :: ", e)
        logger_file.log_error("(userPrescriptionDrugInfo.drx) API ERROR :: {}".format(traceback.format_exc()))

        # API 발송 오류일 경우
        if type(apiResultKey) == bool and not apiResultDatas:
            logger_file.log_error("## (userPrescriptionDrugInfo.drx) API ERROR :: {}".format(apiResultDatas))
            logger_api.send_api_log('', '', userInfo['PharmacyIdx'], 'ERR-201', '(userPrescriptionDrugInfo.drx) API SEND ERROR')
        return False
    else:
        return True

def insert_prescription_send_flag(dataFrame, userInfo, dbConn, flag):
    """
    유저의 처방전 정보 전송 완료 코드 INSERT (LOCAL DB)
    :return:
    """
    try:
        print("##### (처방전 전송결과 저장) 처방전 전송결과를 저장합니다. ")
        print("##### (" + userInfo['CusNm'] + ") 연계회원의 처방전 전송결과를 저장합니다.")
        print("##### (" + userInfo['CusNm'] + ") 회원의 처방전데이터 (" + dataFrame['PrescriptionCd'] + ") 를 전송완료 처리합니다.")

        dbConn.conn_open()
        dataArray = []
        dataArray.append(dataFrame['CusNo'])
        dataArray.append(userInfo['UserId'])
        dataArray.append(dataFrame['PrescriptionCd'])
        dataArray.append("Y")
        dataArray.append("GETDATE()")
        dataArray.append(flag)
        queryResultConfirm = dbConn.send_query_prelink_insert(dataArray)
        dbConn.conn_close()

        if type(queryResultConfirm) == bool and not queryResultConfirm:
            return False

        # print("##### 처방전 전송완료처리 결과 정보 로컬DB 입력 완료")
        # print(queryResultConfirm)

    except Exception as e:
        print("##### (insert_prescription_send_flag) Error :: ", e)
        return False
    else:
        return True

##########################################################################################
####### 스케줄러 프로세스 수행 영역
##########################################################################################

def run_module(root):
    """
    연계모듈 메인 수행 함수
    :param root: GUI 정보
    :return:
    """
    # INI 정보중 청구SW 정보를 기준으로 수행
    confirmUserList = []

    logger_file.log_info("############################################################")
    logger_file.log_info("내손안의약국 조제내역 연계프로세스 환경검사를 시작합니다.")
    if iniDrxsDict['moduletype'] == 'WP':  # 위드팜 청구SW 사용
        # 환경체크 수행
        environmentalReturn = environmental_inspection_part(root)

        # 환경체크 결과값 실패일경우
        if not environmentalReturn:
            root.textInsert("인증실패 :: DB 연결이 실패하였거나, 내손안의약국 약국회원으로 가입되지않은 약국입니다.")
            logger_file.log_error("인증실패 :: DB 연결이 실패하였거나, 내손안의약국 약국회원으로 가입되지않은 약국입니다.")
            # 230816 미니PC용에서는 alert처리하지않기위해 제거함.
            # commonMsg.alertMessage('내손안의약국', '위드팜-내손안의약국 회원약국으로 가입되지않은 약국입니다.')
        else:  # 환경체크 성공
            # 로그 클래스 생성
            # common_log = commonCode.commonLog(userInfoDict['pharmNo'], userInfoDict['saupNo'], userInfoDict['PharmacyIdx'])
            logger_file.log_info("내손안의약국 조제내역 연계프로세스 환경검사를 성공하였습니다.")

            # 로그발송샘플
            # common_log.send_api_log("SUC-001", "샘플발송테스트")
            logger_file.log_info("내손안의약국 조제내역 연계모듈 상태정보를 DRxS로 전송합니다.(send_module_status > WITHPHARM.MODULE_STATUS)")
            print("내손안의약국 조제내역 연계모듈 상태정보를 DRxS로 전송합니다.(send_module_status > WITHPHARM.MODULE_STATUS)")
            status_result_str, description_str = send_module_status('R')     # 모듈 상태정보 API 전송

            if status_result_str:
                logger_file.log_info("내손안의약국 조제내역 연계모듈 상태정보를 DRxS로 전송성공")
            else:
                logger_file.log_info("내손안의약국 조제내역 연계모듈 상태정보를 DRxS로 전송실패 :: {}".format(description_str))

            # TODO 230210 : 서버모듈의 스케줄러로 기능 옮김
            # clear_prescription_info()   # 과거 처방전 접수데이터 중 미처리 데이터 항목 삭제 프로세스

            logger_file.log_info("조제내역 연계대상회원정보를 수집합니다.")
            # 연계대상정보 수집 함수 수행
            confirmUserList = request_server_part(root)

            # 단골회원이 존재하지않을경우 전송부 미수행 리턴
            if type(confirmUserList) == str and confirmUserList == "EMPTY_FAVORITY_MEMBER":
                logger_file.log_info("조제내역 연계대상회원이 존재하지않아 연계프로세스를 수행하지않습니다.")
                return
            elif type(confirmUserList) == bool and not confirmUserList:
                logger_file.log_info("DB가 연결되지않아 연계프로세스를 수행하지않습니다.")
                return

            logger_file.log_info("조제내역 연계대상회원수 :: {} 명".format(len(confirmUserList)))
            # print("##### 최종 연계 대상 회원 목록 :: ", confirmUserList)

            # 최종연계대상회원 + 동명이인 선택완료 회원정보 추가 (221103 주석)
            # finalLinkedUserList = add_confirm_user(confirmUserList, root)

            # 처방전 연계전 연계회원정보(1차,2차승인여부)리스트 내손안의약국 전송 (221103 주석)
            # send_favority_user_info()

            # finalFlag = response_server_part(finalLinkedUserList, root)  # 전송부 함수 수행

            # 수집된 연계대상정보의 조제내역 연계 함수 수행
            logger_file.log_info("조제내역 연계대상회원의 신규 조제내역 검색 및 전송 프로세스 수행")
            finalFlag = response_server_part(list(), root)  # 전송부 함수 수행
            logger_file.log_info("조제내역 연계대상회원의 신규 조제내역 검색 및 전송 프로세스 수행완료")
def proc_start():
    """
    트레이 아이콘 시작 클릭 (모듈 프로세스 시작)
    :return:
    """
    root = windowGUI.GUI()
    root.tkRun()



# 메인 프로세스 시작
if __name__ == '__main__':
    Timer(3, proc_start).start()
    # tray_icon.run()  # pystray 트레이 아이콘 실행

    # 기존
    # root = windowGUI.GUI()
    # root.tkRun()