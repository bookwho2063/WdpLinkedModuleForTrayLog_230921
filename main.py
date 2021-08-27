# -*- coding: utf-8 -*-
#!/usr/bin/python

import sys, os
import time

import schedule
import tkinter as tkinter
from tkinter import *

import commonCode
import connectionDbPyodbc as connDb
import connectionApi as connApi
import readIniFile as readIni
import windowGUI
import threading
import queue

# 모듈 사용 약국정보 딕셔너리 전역변수
userInfoDict = dict()

# 최종연계회원정보리스트 전역변수
userInfoListGlobal = []

# DRxS.ini 파일 정보 추출
iniMng = readIni.Read_Ini(iniPath='resource/DRxS.ini')
iniDrxsDict = iniMng.returnIniDict('DRXS')
iniDatabaseDict = iniMng.returnIniDict('DATABASE')

# 로그 TextBox 영역 라인카운트
lineCount = 0

# 스케줄러 수행 플래그값
scheduleFlag = 'Y'

global PharmNm      # 약국명
global PharmNo      # 약국요양기관번호
global SaupNo       # 약국사업자번호
global PharmIdx     # 약국회원 고유번호 IDX

class ThreadTask(threading.Thread):
    def __init__(self, queue, gui):
        threading.Thread.__init__(self)
        threading.Thread.daemon=True
        self.queue = queue
        self.flag = threading.Event()
        self.gui = gui

    def run(self):
        self.flag.is_set()
        print("##### 스케줄러 실행!! :: flag = ", self.flag)
        run_module(self.gui)

def environmental_inspection_part(gui_root):
    """
    모듈 연계 환경검사 함수
    :param gui_root: GUI 정보
    :return: 환경검사 결과정보
    """
    # TODO : 레지스트리 정보 추출하여 INI파일에 적용 (완)
    common = commonCode.commonCode()
    regValue, regType = common.read_regist("SERVER")


    print("##### iniDrxsDict_DRXS :: ", iniDrxsDict)
    print("##### iniDatabaseDict_DATABASE :: ", iniDatabaseDict)
    gui_root.textInsert("위드팜 - 내손안의약국 처방전 연계프로세스 환경검사를 수행합니다.")

    # DB 연동 테스트
    # dbConn = connDb.Manage_logcal_db(iniDatabaseDict['server'], iniDatabaseDict['database'], iniDatabaseDict['username'], iniDatabaseDict['password'])
    dbConn = connDb.Manage_logcal_db(regValue, iniDatabaseDict['database'], iniDatabaseDict['username'], iniDatabaseDict['password'])
    dbConn.conn_open()
    dbConnFlag = dbConn.send_sample_query()

    if dbConnFlag == False:
        print('##### (환경검사) 샘플쿼리 동작 오류로 프로세스 종료')
        gui_root.textInsert("ERROR :: 데이터베이스 접근 오류로 프로세스를 종료합니다.")
        return False
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

    # API 서버 커넥션 체크
    mngApi = connApi.api_manager()
    # 등록 약국 1차 검증
    checkUrl = iniDrxsDict['apiurl'] + '/apiServerConn.drx?PharmNo='+queryResult.iloc[0][1]+'&SaupNo='+queryResult.iloc[0][2]
    # print('##### checkUrl :: ', checkUrl)
    if mngApi.api_conn_check(checkUrl) == "NO_USER":
        gui_root.textInsert("INFO :: 위드팜 - 내손안의약국 연계 회원이 아닙니다.")
        return False

    # API를 이용하여 내손안의약국 약국회원 인증 2차검증
    certifiApiUrl = iniDrxsDict['apiurl']+'/authCheck.drx?PharmNm='+queryResult.iloc[0][0]+'&PharmNo='+queryResult.iloc[0][1]+'&SaupNo='+queryResult.iloc[0][2]+'&PharmSwType='+iniDrxsDict['moduletype']
    certifiApiKeys, certifiApiDic = mngApi.api_conn(certifiApiUrl)
    # TODO 회원인증정보에서 연계기준일자(가입일자)를 추가로 받고 해당 날자 이후로 연계회원정보 및 처방전 정보를 확인할 것

    splitTemp = certifiApiDic['LinkTargetDate'].split(' ')
    certifiApiDic['LinkTargetDate'] = splitTemp[0]
    del(splitTemp)      # 사용하지않는 변수 삭제
    print("##### 회원인증 결과 정보(KEY) :: ", certifiApiKeys)
    print("##### 회원인증 결과 정보(VALUE) :: ", certifiApiDic)

    # 회원약국 체크 후 결과 값 검증
    if certifiApiDic['Status'] == 'error':
        print("##### (환경검사) 회원약국이 아닙니다.")
        gui_root.textInsert("INFO :: 위드팜 - 내손안의약국 연계 회원이 아닙니다.")
    elif certifiApiDic['Status'] == 'ok':
        print("##### (환경검사) {} 약국회원 인증 완료!! ".format(queryResult.iloc[0][0]))
        gui_root.textInsert(str("내손안의약국 연계회원 \'{}\' 약국의 인증을 완료하였습니다.".format(queryResult.iloc[0][0])))
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

        print("##### 회원 인증 후 userInfoDict :: ", userInfoDict)
        return True

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
    # API 클래스 생성
    mngApi = connApi.api_manager()

    # 약국회원정보를 이용하여 회원약국의 내손안의약국 단골회원을 조회한다.
    # print("##### 약국회원정보 :: ", userInfoDict)
    ## TODO : checkUrl 의 마지막 인자 (약국회원가입일자) 하드코딩된 것 변경해야함 (210701)
    ## TODO : checkUrl 의 마지막 인자 (약국회원가입일자) 빼는게 나을듯, 언제 이후 회원을 받을 필요가 없음 (210727)
    gui_root.textInsert("처방전 연계를 위하여 약국회원의 단골회원정보를 요청합니다.")
    checkUrl = iniDrxsDict['apiurl'] + "/favoritUserList.drx?PharmacyIdx="+userInfoDict['PharmacyIdx']+"&PharmNo="+userInfoDict['pharmNo']+"&SaupNo="+userInfoDict['saupNo']+"&GetDate=20210520"
    # print("##### checkUrl :: ", checkUrl)
    userInfoKey, userInfoList = mngApi.api_conn(checkUrl)
    # print("##### 연계대상목록요청정보키(userInfoKey) :: ", userInfoKey)
    # print("##### 연계대상목록요청정보(userInfoList) :: ", userInfoList)
    # print("##### 연계대상목록요청정보갯수(userInfoList.count) :: ", userInfoList['DataCount'])

    # 필요 변수 생성
    sameUserList = []
    resultUserList = []

    # 연계대상 회원목록
    for item in userInfoList['Items']:  # items 내 값 추출
        # 생년월일이 8자리일경우 6자리로 변경
        if len(item['birth']) == 8:
            temp = item['birth']
            item['birth'] = temp[2:]
        # 연계대상회원목록
        # print('##### item :: ', item)
        # print('##### item.id :: ', item['idx'])
        # print('##### item.userName :: ', item['user_name'])
        # print('##### item.mobile :: ', item['mobile'])
        # print('##### item.birth :: ', item['birth'])
        # print('##### item.regi_date :: ', item['regi_date'])

        # 개별로 연계대상회원이 약국 로컬 DB에 존재하는지 확인
        gui_root.textInsert(str(item['user_name']+" 회원의 본인여부를 판별합니다."))
        # gui_root.textInsert()
        userInfoQuery = []
        userInfoQuery.append("SELECT")
        userInfoQuery.append("CusNo")
        userInfoQuery.append(", FamNo")
        userInfoQuery.append(", CusNm")
        userInfoQuery.append(", CusJmno")
        userInfoQuery.append(", RealBirth")
        userInfoQuery.append(", Sex")
        userInfoQuery.append(", HpTel")
        userInfoQuery.append("FROM dbo.PatientCustomers")
        userInfoQuery.append("WHERE RealBirth = '"+item['birth']+"'")
        userInfoQuery.append("AND CusNm = '"+item['user_name']+"'")
        userInfoQuery.append("AND Sex = '"+item['sex']+"'")
        userInfoQueryStr = " ".join(userInfoQuery)

        dbConn = connDb.Manage_logcal_db(iniDatabaseDict['server'], iniDatabaseDict['database'], iniDatabaseDict['username'], iniDatabaseDict['password'])
        dbConn.conn_open()
        quertResultDf = dbConn.send_query(userInfoQueryStr)
        dbConn.conn_close()
        # print("##### quertResultDf :: \n", quertResultDf)
        # print("##### quertResultDf,len :: \n", len(quertResultDf))
        # 비교 후 데이터가 있는 df의 경우 별도로 저장해둘것 (회원여부판별)
        if quertResultDf.empty == True:
            gui_root.textInsert(str(item['user_name']+" 회원은 약국방문이력이 존재하지않은 회원입니다."))
            continue

        # 회원정보가 존재하지만 동명이인이고 생년월일과 성별까지 같을 경우 결과값이 1보다 크므로 해당 인원은 제외
        # TODO 이름, 생년월일, 성별까지 같은 사용자의 경우 판별할 수 없으므로 해당인원의 연계는 제한한다, 수동으로 DB 확인 후 처리하도록 한다.
        if len(quertResultDf) > 1:
            print("##### (요청부) 연계회원 중 동명이인 회원이 존재합니다. 해당정보를 제외하고 연계회원을 구축합니다.")
            gui_root.textInsert(str(item['user_name']+" 회원은 동명이인 정보가 조회되어 최종연계회원에서 제외합니다."))
            for idx in len(quertResultDf):
                sameUserDict = dict()
                sameUserDict['CusNo'] = quertResultDf.iloc[idx][0]
                sameUserDict['FamNo'] = quertResultDf.iloc[idx][1]
                sameUserDict['CusNm'] = quertResultDf.iloc[idx][2]
                sameUserDict['CusJmno'] = quertResultDf.iloc[idx][3]
                sameUserDict['RealBirth'] = quertResultDf.iloc[idx][4]
                sameUserDict['Sex'] = quertResultDf.iloc[idx][5]
                sameUserDict['UserId'] = item['idx']
                sameUserDict['UserName'] = item['user_name']
                sameUserDict['Mobile'] = item['mobile']
                sameUserDict['birth'] = item['birth']
                sameUserDict['regi_date'] = item['regi_date']
                sameUserList.append(sameUserDict)
                # TODO 중복예상회원정보 별도 처리 프로세스 필요함 (미완료)

        # TODO : 일반회원의 내손안의 약국 승인정보 존재여부 확인 SELECT (완료)
        print("##### 연계 예정 회원("+quertResultDf.iloc[0][2]+")님의 연계승인정보를 조회합니다.")
        dbConn.conn_open()
        tempQuery = []
        tempQuery.append('SELECT CusNo, PharmAuthFlag, CustomerAuthFlag FROM dbo.DrxsCustomersAuth')
        tempQuery.append("WHERE CusNo = '" + quertResultDf.iloc[0][0] + "'")
        sendSql = " ".join(tempQuery)
        queryResult = dbConn.send_query(sendSql)
        dbConn.conn_close()

        if len(queryResult) == 0:
            # TODO : 신규연계회원 회원의 연계승인 플래그 최초저장 (완료)
            gui_root.textInsert(str("신규연계회원("+quertResultDf.iloc[0][2]+")님의 연계신청정보를 데이터베이스에 저장합니다."))
            print("##### 신규연계회원("+quertResultDf.iloc[0][2]+")님의 플래그정보를 INSERT 처리합니다.")
            dbConn.conn_open()
            tempQuery = []
            tempQuery.append(quertResultDf.iloc[0][0])
            tempQuery.append(item['idx'])
            tempQuery.append('Y')
            queryResult = dbConn.send_query_authinfo_insert(tempQuery)
            dbConn.conn_close()
        elif len(queryResult) == 1:
            # TODO : 기존연계회원 회원의 약국연계승인 플래그 검증 (완료)
            print("##### 기존연계회원("+quertResultDf.iloc[0][2]+")님의 플래그정보를 검증 처리합니다.")
            gui_root.textInsert(str("기존연계회원(" + quertResultDf.iloc[0][2] + ")님의 연계신청정보를 검증 처리합니다."))
            if queryResult.iloc[0][1] == None:
                # TODO : 기존연계회원 회원의 약국연계승인 플래그 미존재시 처방전 연계 회원목록으로 추가하지않음 (완료)
                print("##### 기존연계회원("+quertResultDf.iloc[0][2]+")님은 약사님의 연계승인이 이뤄지지 않았습니다.")
                gui_root.textInsert(str("기존연계회원("+quertResultDf.iloc[0][2]+")님은 약사님의 연계승인이 이뤄지지 않았습니다."))
                continue
            elif queryResult.iloc[0][1] == 'Y' or queryResult.iloc[0][1] == 'y':
                # TODO : 기존연계회원 회원의 약국연계승인완료시 회원정보(휴대전화번호)업데이트 및 처방전 연계 최종대상으로 추가 (완료)
                print("##### 기존연계회원(" + quertResultDf.iloc[0][2] + ")님은 약사님의 연계승인이 완료되었습니다.")
                gui_root.textInsert(str("기존연계회원(" + quertResultDf.iloc[0][2] + ")님은 약사님의 연계승인이 완료되었습니다."))

                print("##### 기존연계회원(" + quertResultDf.iloc[0][2] + ")님의 회원정보를 로컬DB에 업데이트 처리합니다.")
                gui_root.textInsert(str("기존연계회원(" + quertResultDf.iloc[0][2] + ")님의 회원정보를 로컬DB에 업데이트 처리합니다."))

                # 모바일 정보 업데이트 (정보 업데이트 하지말자고하셔서 주석처리)
                # tempMobile = item['mobile']
                # print("##### 기존연계회원(" + quertResultDf.iloc[0][2] + ")님의 휴대전화번호 파싱 : ", tempMobile[0:3]+"-"+tempMobile[3:7]+"-"+tempMobile[7:])
                # dbConn.conn_open()
                # tempQuery = []
                # tempQuery.append(tempMobile)
                # tempQuery.append(quertResultDf.iloc[0][0])
                # queryResult = dbConn.send_query_userinfo_update(tempQuery)
                # dbConn.conn_close()

                # 검증완료된 유저정보 저장, 단일1인일 경우(전역변수)
                compUserInfoDict = dict()
                compUserInfoDict['CusNo'] = quertResultDf.iloc[0][0]
                compUserInfoDict['FamNo'] = quertResultDf.iloc[0][1]
                compUserInfoDict['CusNm'] = quertResultDf.iloc[0][2]
                compUserInfoDict['CusJmno'] = quertResultDf.iloc[0][3]
                compUserInfoDict['RealBirth'] = quertResultDf.iloc[0][4]
                compUserInfoDict['Sex'] = quertResultDf.iloc[0][5]
                compUserInfoDict['UserId'] = item['idx']
                compUserInfoDict['UserName'] = item['user_name']
                compUserInfoDict['Mobile'] = item['mobile']
                compUserInfoDict['birth'] = item['birth']
                compUserInfoDict['regi_date'] = item['regi_date']
                userInfoListGlobal.append(compUserInfoDict)

                # 단일로 검증된 연계회원정보를 최종연계 대상 리스트에 추가 resultUserList
                resultUserList.append(quertResultDf.to_dict())

    # print("##### 최종 처방전 연계승인 회원 수 :: ", len(resultUserList))
    # print("##### 최종 처방전 연계승인 회원 정보 :: ")
    # print(*resultUserList, sep='\n')


    # TODO 회원판별된 대상의 개인정보 LOCAL DB 업데이트 (위드팜에서 회원정보 업데이트 하지말아달라고함, 휴대전화번호 등)

    return resultUserList

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
    gui_root.textInsert("최종연계대상의 처방전 정보를 연계하는 프로세스를 시작합니다.")
    common = commonCode.commonCode()
    mngApi = connApi.api_manager()  # API 전송을 위한 커넥션 생성
    dbConn = connDb.Manage_logcal_db(iniDatabaseDict['server'], iniDatabaseDict['database'],iniDatabaseDict['username'], iniDatabaseDict['password'])
    # print("##### 1111111111111")
    # print("##### userInfoListGlobal :: ", userInfoListGlobal)
    # print("##### userInfoList :: ", userInfoList)

    # 연계 유저별 루프
    for userInfo in userInfoListGlobal:
        ################################################
        # 1. 유저의 처방전 정보 조회 & 처방전 전송
        # gui_root.textInsert(str(""))
        userInfo['PharmacyIdx'] = str(PharmIdx)     #유저정보에 약국의 IDX 코드를 삽입
        gui_root.textInsert(str(userInfo['CusNm']+" 사용자의 처방전 정보를 조회합니다."))
        queryArr = []
        queryArr.append("SELECT")
        queryArr.append("A.PrescriptionCd, A.CusNo, A.InsuGb, A.CareGb, A.InsuEtc, A.SendGb, A.RootCusNm, A.PromissNo, A.InsuNo, A.CusNm, A.CusJmno, A.HospitalNo, A.Doctor, A.DoctorSeq")
        queryArr.append(", CONVERT(VARCHAR, A.MakeDte, 23) AS MakeDte, A.PregYn, A.MakeDay, A.ConDay, CONVERT(VARCHAR, A.PresDte, 23) AS PresDte, A.PresNo, A.UseDay, A.DisCd1, A.DisCd2, A.SpecialCd, A.LicenseNo, A.BabyYn, A.OverTime, A.UserTime, A.StateGb")
        queryArr.append(", A.CareHospitalGb, CONVERT(VARCHAR, A.RDte, 120) AS RDte, A.RUser, CONVERT(VARCHAR, A.MDte, 120) AS MDte, A.MUser, CONVERT(VARCHAR, A.CDte, 120) AS CDte, A.CUser, A.DelYn, A.ErrGb, A.LabelYn, A.PrescriptionSeq, A.PosPayGb, A.NimsGb, A.PowderYn, B.TransStatus, B.TransDt")
        queryArr.append("FROM dbo.Prescription AS A")
        queryArr.append("LEFT OUTER JOIN dbo.DrxsPrescriptionLinkInfo AS B")
        queryArr.append("ON A.PrescriptionCd = B.PrescriptionCd")
        queryArr.append("WHERE A.CusNo = '"+userInfo['CusNo']+"'")
        # TODO 여기 아래 날자 바꿔야함. (내부 협의 후 날자 선정 필요함), 연계회원(약국)이 내손안의약국에 가입한 날자를 기준으로 하면 좋을듯
        queryArr.append("AND A.PresDte BETWEEN CONVERT(DATE, '200101') AND CONVERT(CHAR(10), GETDATE(), 23)")   # 날자를 해당 회원이 내손안의약국에 연계 동의한 날자로 바꿔줘야함
        queryArr.append("AND B.PrescriptionCd IS NULL")   # 전송완료 테이블에 존재하는 처방전 데이터는 재전송하지않기 위해 제외
        queryStr = " ".join(queryArr)

        dbConn.conn_open()
        queryResultPrescription = dbConn.send_query(queryStr)
        dbConn.conn_close()

        if queryResultPrescription.empty == True:
            # print("##### ("+userInfo['CusNm']+") 해당 연계회원은 처방전 내역이 존재하지않습니다.")
            gui_root.textInsert(str(userInfo['CusNm'] + " 사용자는 처방전 정보가 존재하지않습니다."))
            continue

        # print("##### 연계회원 (" + userInfo['CusNm'] + ") 님 처방전 조회 결과 #####")
        # print(queryResultPrescription)

        splitCount = 3  # 처방전 분할 갯수
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
                send_prescription(tempDataframe, userInfo, dbConn, mngApi)  # 처방전 데이터프레임 API 전송

                for index, row in tempDataframe.iterrows():
                    gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 처방전 청구정보를 전송합니다."))
                    resultFlag = send_prescription_amt(row, userInfo, dbConn, mngApi)  # 처방전 청구정보 조회 및 API 전송
                    if resultFlag != False:
                        gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 처방전 약정보를 전송합니다."))
                        resultFlag = send_prescription_drug(row, userInfo, dbConn, mngApi)  # 처방전 약정보 조회 및 API 전송
                        if resultFlag != False:
                            gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리를 진행합니다."))
                            resultFlag = insert_prescription_send_flag(row, userInfo, dbConn)  # 처방전 전송완료 처리(로컬DB)
                            if resultFlag == False:
                                gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리중 오류가발생하였습니다."))
                                print("##### 처방전 전송완료 로컬플래그처리 실패!!!")
                        else:
                            gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 약정보 전송처리중 오류가발생하였습니다."))
                            print("##### 처방전 약정보 전송 실패!!!")
                    else:
                        gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 청구정보 전송처리중 오류가발생하였습니다."))
                        print("##### 처방전 청구정보 전송 실패!!!")

            else:
                # (분할전송) 처방전 정보
                # print("##### (" + userInfo['CusNm'] + ") 분할한 tempDataframe 타입 :: ", type(tempDataframe))
                # print("##### (" + userInfo['CusNm'] + ") 분할한 tempDataframe 데이터 :: ", tempDataframe)

                gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 정보를 전송합니다."))
                send_prescription(tempDataframe, userInfo, dbConn, mngApi)      # 처방전 데이터프레임 API 전송

                # (분할전송) 처방전 청구정보 및 처방전 약정보
                for index, row in tempDataframe.iterrows():
                    gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 청구정보를 전송합니다."))
                    resultFlag = send_prescription_amt(row, userInfo, dbConn, mngApi)        # 처방전 청구정보 조회 및 API 전송
                    if resultFlag != False:
                        gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 약정보를 전송합니다."))
                        resultFlag = send_prescription_drug(row, userInfo, dbConn, mngApi)       # 처방전 약정보 조회 및 API 전송
                        if resultFlag != False:
                            gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리를 진행합니다."))
                            resultFlag = insert_prescription_send_flag(row, userInfo, dbConn)  # 처방전 전송완료 처리(로컬DB)
                            if resultFlag == False:
                                gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 전송완료처리중 오류가발생하였습니다."))
                                print("##### 처방전 전송완료 로컬플래그처리 실패!!!")
                        else:
                            gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 약정보전송처리중 오류가발생하였습니다."))
                            print("##### 처방전 약정보 전송 실패!!!")
                    else:
                        gui_root.textInsert(str(userInfo['CusNm'] + " 사용자의 대상 처방전 청구정보 전송처리중 오류가발생하였습니다."))
                        print("##### 처방전 청구정보 전송 실패!!!")


##########################################################################################
####### 처방전(내역,가격,약물)정보 조회 및 API 전송 (위드팜)
##########################################################################################

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
        checkUrl = iniDrxsDict['apiurl'] + '/userPrescription.drx'  # 처방전 전송 API URL
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrl, transJsonStr)  # 처방전 POST 방식 전송
        return True
    except Exception as e:
        print("##### (send_prescription) Error :: ", e)
        return False
        
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

    try:
        common = commonCode.commonCode()
        # 처방전 청구가격정보 쿼리
        print("##### (청구가격정보) dataFrame :: ", dataFrame)
        print("##### (청구가격정보) type(dataFrame) :: ", type(dataFrame))

        print("##### 처방전 고유번호 (" + dataFrame['PrescriptionCd'] + ")")
        queryArr = []
        queryArr.append("SELECT")
        queryArr.append("PrescriptionCd , tAmt1, sAmt, BillAmt, SupportAmt, tAmt2, mBillAmt, DrugDiffAmt, TotAmt, t100Amt, mAmt, t100mAmt, s100mAmt")
        queryArr.append(", Bill100mtAmt, Bill100mmAmt, Rate, TotalSelfAmt, mTotBAmt, mBillBAmt, TotalAmt, BExcept")
        queryArr.append("FROM dbo.PrescriptionAmt")
        # 인자값 바꿔줘야함 제일처음 처방전 쿼리결과에서..
        queryArr.append("WHERE PrescriptionCd = '" + dataFrame['PrescriptionCd'] + "'")
        queryStr = " ".join(queryArr)

        dbConn.conn_open()
        queryResultAmt = dbConn.send_query(queryStr)
        dbConn.conn_close()

        print("##### (" + userInfo['CusNm'] + ") 처방전 가격정보 ")
        print(queryResultAmt)

        if len(queryResultAmt) == 0:  # 처방전 청구정보 존재여부확인
            print("##### (" + userInfo['CusNm'] + ")님의 처방전(" + dataFrame['PrescriptionCd'] + ")청구가격정보가 존재하지않습니다.")

        transJsonStrAmt = common.packageJsonPrescriptionAmt(queryResultAmt, userInfo)
        # print("##### (처방전 청구정보전송-분할) transJsonStrAmt :: ", transJsonStrAmt)

        checkUrlAmt = iniDrxsDict['apiurl'] + '/userPrescriptionAmt.drx'
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrlAmt, transJsonStrAmt)  # POST 방식 전송
        print("##### (처방전-분할 청구정보) 일괄전송결과 apiResultKey :: ", apiResultKey)
        print("##### (처방전-분할 청구정보) 일괄전송결과 apiResultDatas :: ", apiResultDatas)

        return True
    except Exception as e:
        print("##### (send_prescription_amt) Error :: ", e)
        return False

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
        print("##### (약정보) dataFrame :: ", dataFrame)
        print("##### (약정보) type(dataFrame) :: ", type(dataFrame))

        print("##### 처방전 고유번호 (" + dataFrame['PrescriptionCd'] + ")")
        queryArr = []
        queryArr.append("SELECT")
        queryArr.append(
            "a.PrescriptionCd , a.Seq, a.Gb, a.ItemType, a.ItemCd, a.Price, a.EatDay, a.TotDay, a.EatOnce, a.TotQty, a.Amt, a.MaxAmt, a.DrugDiffAmt")
        queryArr.append(", MakeGb, EatGb, PasYn, LinkLabel, ItemSeq")
        queryArr.append(", ISNULL((SELECT EatNm FROM dbo.InfoDrugEat WHERE EatCd = a.EatGb), '') AS EatComment")
        queryArr.append("FROM dbo.PrescriptionDrugMake AS a")
        # 인자값 바꿔줘야함 제일처음 처방전 쿼리결과에서..
        queryArr.append("WHERE PrescriptionCd = '" + dataFrame['PrescriptionCd'] + "'")
        # 날자를 해당 회원이 내손안의약국에 연계 동의한 날자로 바꿔줘야함
        queryStr = " ".join(queryArr)

        dbConn.conn_open()
        queryResultDrug = dbConn.send_query(queryStr)
        dbConn.conn_close()

        print("##### (" + userInfo['CusNm'] + ") 처방전 약물정보 ")
        print(queryResultDrug)

        if len(queryResultDrug) == 0:  # 처방전 청구정보 존재여부확인
            print("##### (" + userInfo['CusNm'] + ")님의 처방전(" + dataFrame['PrescriptionCd'] + ")약정보가 존재하지않습니다.")

        transJsonStrDrug = common.packageJsonPrescriptionDrug(queryResultDrug, userInfo)
        # print("##### (처방전 약물정보전송-분할) transJsonStrDrug :: ", transJsonStrDrug)

        checkUrlAmt = iniDrxsDict['apiurl'] + '/userPrescriptionDrugInfo.drx'
        apiResultKey, apiResultDatas = mngApi.api_conn_post(checkUrlAmt, transJsonStrDrug)  # POST 방식 전송
        print("##### (처방전-분할 약물정보) 일괄전송결과 apiResultKey :: ", apiResultKey)
        print("##### (처방전-분할 약물정보) 일괄전송결과 apiResultDatas :: ", apiResultDatas)

        return True
    except Exception as e:
        print("##### (send_prescription_drug) Error :: ", e)
        return False

def insert_prescription_send_flag(dataFrame, userInfo, dbConn):
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
        queryResultConfirm = dbConn.send_query_prelink_insert(dataArray)
        dbConn.conn_close()
        print("##### 처방전 전송완료처리 결과 정보 로컬DB 입력 완료")
        # print(queryResultConfirm)
        return True
    except Exception as e:
        print("##### (insert_prescription_send_flag) Error :: ", e)
        return False

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

    if iniDrxsDict['moduletype'] == 'WP':  # 위드팜 청구SW 사용
        # 환경체크 수행
        environmentalReturn = environmental_inspection_part(root)

        # 환경체크 결과값 실패일경우
        if environmentalReturn == False:
            root.textInsert("인증실패 :: 해당 약국은 현재 내손안의약국 약국회원으로 가입되지않은 회원사입니다.")
        else:  # 환경체크 성공
            root.textInsert("위드팜 - 내손안의약국 처방전 연계프로세스 환경검사를 성공하였습니다.")
            root.textInsert("----- 위드팜 회원약국 정보 -----")
            root.textInsert(str("약국명 : {}".format(userInfoDict['pharmNm'])))
            root.textInsert(str("대표명 : {}".format(userInfoDict['ceoNm'])))
            root.textInsert(str("내손안의약국 ID : {}".format(userInfoDict['PharmacyIdx'])))
            root.textInsert("-----------------------------")
            # print("##### 접속한 약국의 회원정보 (위드팜) :: ", userInfoDict)  # 모듈사용중인 약국회원 정보 (전역변수)
            root.textInsert("처방전 연계를 위한 연계요청프로세스를 시작합니다.")
            confirmUserList = request_server_part(root)  # 요청부 함수 수행
            # print("##### 최종 연계 대상 회원 목록 :: ", confirmUserList)

            finalFlag = response_server_part(confirmUserList, root)  # 전송부 함수 수행

# 메인 프로세스 시작
if __name__ == '__main__':
    root = windowGUI.GUI()
    root.tkRun()
