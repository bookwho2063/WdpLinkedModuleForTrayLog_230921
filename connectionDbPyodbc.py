import sys
import pyodbc
import windowMsgCommon as commonMsg
import pandas as pd

"""
# 필요 쿼리 목록
# 1. 약국회원정보 조회 (위드팜/약정원)
SELECT
	CusNo
	, CusNm
	, HpTel
FROM dbo.PatientCustomers

# 단골회원의 약국방문기록 확인
SELECT 
	CusNo 
	, FamNo 
	, CusNm 
	, CusJmno 
	, RealBirth
	, Email
	, ZipCd
	, Add1
	, Add2
	, HomeTel
	, HpTel
	, Relation
	, PromissNo
	, CertiNo
	, RootCusNm
	, CusInfo
	, JmnoChk
	, SysDte
	, SysUsr
	, FirstDt
	, Sex
	, EngCusNm
	, ForeignNo
	, PassPortNo
FROM dbo.PatientCustomers
WHERE RealBirth = ''
AND CusNm = ''
AND Sex = ''
   
# 2. 단골회원정보 조회 (로컬DB -> 위드팜/약정원)
SELECT 
	PC.CusNo 
	, PC.FamNo 
	, PC.CusNm 
	, PC.CusJmno 
	, PC.RealBirth 
	, PC.Email 
	, PC.ZipCd 
	, PC.Add1 
	, PC.Add2 
	, PC.HomeTel 
	, PC.HpTel 
	, PC.Relation 
	, PC.PromissNo 
	, PC.CertiNo 
	, PC.RootCusNm 
	, PC.CusInfo 
	, PC.JmnoChk 
	, PC.SysDte 
	, PC.SysUsr 
	, PC.FirstDt 
	, PC.Sex 
	, PC.EngCusNm 
	, PC.ForeignNo 
	, PC.PassPortNo 
	, DC.PharmAuthFlag
	, DC.CustomerAuthFlag
	, DC.PharmAuthDte
	, DC.CustomerAuthDte
FROM dbo.PatientCustomers AS PC
INNER JOIN dbo.DrxsCustomersAuth AS DC
ON DC.CusNo = PC.CusNo
WHERE DC.CustomerAuthFlag = 'Y'

# 3. 단골회원 휴대전화번호 업데이트 (로컬DB -> 위드팜/약정원)
UPDATE dbo.PatientCustomers
SET
	HpTel = '01028501490'
WHERE CusNo = 'C20200400001'


# 4. 단골회원의 처방전 내역 조회 (로컬DB -> 위드팜/약정원)
SELECT 
	PrescriptionCd 
	, CusNo 
	, InsuGb 
	, CareGb 
	, InsuEtc 
	, SendGb 
	, RootCusNm 
	, PromissNo 
	, InsuNo 
	, CusNm 
	, CusJmno 
	, HospitalNo 
	, Doctor 
	, DoctorSeq 
	, MakeDte 
	, PregYn 
	, MakeDay 
	, ConDay 
	, PresDte 
	, PresNo 
	, UseDay 
	, DisCd1 
	, DisCd2 
	, SpecialCd 
	, LicenseNo 
	, BabyYn 
	, OverTime 
	, UserTime 
	, StateGb 
	, CareHospitalGb 
	, RDte 
	, RUser 
	, MDte 
	, MUser 
	, CDte 
	, CUser 
	, DelYn 
	, ErrGb 
	, LabelYn 
	, PrescriptionSeq 
	, NimsGb 
	, PowderYn 
FROM dbo.Prescription
WHERE CusNo = ''
AND CONVERT(DATE, MakeDte) >= CONVERT(DATE, '날짜8자리')

# 5. 단골회원의 처방전 결재내역 조회 (로컬DB -> 위드팜/약정원)
SELECT  
	PrescriptionCd 
	, tAmt1 
	, sAmt 
	, BillAmt 
	, SupportAmt 
	, tAmt2 
	, mBillAmt 
	, DrugDiffAmt 
	, TotAmt 
	, t100Amt 
	, mAmt 
	, t100mAmt 
	, s100mAmt 
	, Bill100mtAmt 
	, Bill100mmAmt 
	, Rate 
	, TotalSelfAmt 
	, mTotBAmt 
	, mBillBAmt 
	, TotalAmt 
	, BExcept 
FROM dbo.PrescriptionAmt
WHERE PrescriptionCd = 'A20200300001'
"""

class Manage_logcal_db:
    """
    NOTE : 로컬 MS-SQL 관리 클래스
    DATE : 2021.04.26
    AUTH : JW
    """
    conn = ''
    cursor = ''

    def __init__(self, server, database, username, password):
        """
        MS-SQL 관리 클래스 초기화
        :param server: 서버정보 (localhost\TOOD2008)
        :param database: 데이터베이스정보 WithpharmErp
        :param username: 접속ID
        :param password: 접속PW
        """
        self.server = server
        self.database = database
        self.username = username
        self.password = password

    def conn_open(self):
        """
        MS-SQL 커넥션 생성
        :return:
        """
        try:
            self.conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + self.server + ';DATABASE=' + self.database + ';UID=' + self.username + ';PWD=' + self.password)
            self.cursor = self.conn.cursor()
            print('##### connection Success!!')
            #commonMsg.alertMessage('내손안의약국', '로컬 DB 연결성공')
        except pyodbc.Error as e:
            print('##### connection Error!!')
            commonMsg.alertMessage('내손안의약국', '로컬 DB 연결실패!\n관리자문의바랍니다.')
            sys.exit("Local Database Not Connection")

    def conn_close(self):
        """
        MS-SQL 커넥션 종료
        :return:
        """
        try:
            self.conn.close()
            print("##### DB Connection Close Success!!")
        except pyodbc.Error as e:
            print("##### DB Connection Close Error!! :: ", e)
            commonMsg.alertMessage('내손안의약국', '로컬 DB 연결종료실패!\n관리자문의바랍니다.')
            sys.exit("Local Database Close Failed")

    def send_sample_query(self):
        """
        연결확인용 샘플 쿼리를 전송합니다.
        :return:
        """
        print("##### 샘플 쿼리를 전송하여 DB 상태를 확인합니다.")
        queryArr = []
        queryArr.append("SELECT")
        queryArr.append("1")
        # queryArr.append("CusNo,")
        # queryArr.append("CusNm,")
        # queryArr.append("HpTel")
        # queryArr.append("FROM dbo.PatientCustomers")
        queryStr = " ".join(queryArr)

        # print("query result :: ", queryResultArr)
        dataFrame = pd.read_sql_query(queryStr, self.conn)
        # print("##### dataFrame :: ", dataFrame)
        # print("##### dataFrame.len :: ", len(dataFrame))
        # print("##### dataFrame.empty :: ", dataFrame.empty)
        if dataFrame.empty == True:
            return False
        else:
            return True

        # for idx, row in dataFrame.iterrows():
        #     print("CusNo 값 :: ", row.CusNo)
        #     print("CusNm 값 :: ", row.CusNm)
        #     print("HpTel 값 :: ", row.HpTel)
        #     print("=====================================")

    def send_query(self, queryArr):
        """
        쿼리를 전송합니다.
        :param queryArr:
        :return:
        """
        print("##### (send_query) Query :: ", queryArr)

        dataFrame = pd.read_sql_query(queryArr, self.conn)
        # print("##### dataFrame :: ", dataFrame)
        # print("##### dataFrame.len :: ", len(dataFrame))
        # print("##### dataFrame.empty :: ", dataFrame.empty)

        # self.cursor.execute(queryArr)
        #
        # queryResultArr = []
        # for row in self.cursor:
        #     queryResultArr.append(row)
        #
        # print("##### 쿼리 결과입니다 :: ", queryResultArr)
        # print("##### 쿼리 결과length :: ", len(queryResultArr))
        return dataFrame

    def send_query_prelink_insert(self, dataArray):
        """
        처방전 최종연계결과 플래그적용 INSERT 쿼리를 전송합니다.
        :param queryArr: SQL String
        :return: 전송결과
        """
        try:
            count = self.cursor.execute("""INSERT INTO dbo.DrxsPrescriptionLinkInfo (CusNo, UserId, PrescriptionCd, TransStatus) VALUES (?,?,?,?)""", dataArray[0], dataArray[1], dataArray[2], dataArray[3])
            self.conn.commit()
        except Exception as e:
            print("##### (send_query_insert) Error :: ", e)



    def send_query_authinfo_insert(self, dataArray):
        """
        신규연계회원의 연계플래그정보를 INSERT 처리한다.
        :param queryArr: SQL String
        :return: 전송결과
        """
        try:
            count = self.cursor.execute("""INSERT INTO dbo.DrxsCustomersAuth (CusNo, UserId, CustomerAuthFlag, PharmAuthFlag, CustomerAuthDte) VALUES (?,?,?,'N',GETDATE())""", dataArray[0], dataArray[1], dataArray[2])
            self.conn.commit()
        except Exception as e:
            print("##### (send_query_authinfo_insert) Error :: ", e)

    def send_query_userAuth_update(self, dataArray):
        """
        일반회원의 연계승인정보 업데이트
        :param dataArray:
        :return:
        """
        try:
            count = self.cursor.execute("""UPDATE dbo.DrxsCustomersAuth SET CustomerAuthFlag = ?, CustomerAuthDte = GETDATE() WHERE CusNo = ?""", dataArray[0], dataArray[1])
            self.conn.commit()
        except Exception as e:
            print("##### (send_query_userAuth_update) Error :: ", e)
            
    def send_query_userinfo_update(self, dataArray):
        """
        연계회원의 개인정보(휴대전화번호 등)을 최신화하기위하여 업데이트 처리
        :param dataArray:
        :return:
        """
        try:
            count = self.cursor.execute("""UPDATE dbo.PatientCustomers SET HpTel = ? WHERE CusNo = ?""", dataArray[0], dataArray[1])
            self.conn.commit()
        except Exception as e:
            print("##### (send_query_userinfo_update) Error :: ", e)



# 클래스 사용 테스트
# if __name__ == '__main__':
#     print('##### DB 커넥션 체크')
#     server = 'localhost\TOOD2008'
#     database = 'WithpharmErp'
#     username = 'sa'
#     password = '$dnlemvka3300$32!'
#
#
#     ## class 타입 테스트
#     CusNm = '박준욱'
#     quertArr = []
#     quertArr.append("SELECT")
#     quertArr.append("*")
#     quertArr.append("FROM dbo.PatientCustomers")
#     quertArr.append("WHERE CusNm = '" + CusNm + "'")
#     queryStr = " ".join(quertArr)
#
#     dbMng = Manage_logcal_db(server, database, username, password)
#     dbMng.conn_open()
#     dbMng.send_query(queryStr)
#     dbMng.conn_close()
