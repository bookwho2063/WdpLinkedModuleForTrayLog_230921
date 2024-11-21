import sys
import time

import pyodbc
import pandas as pd
import traceback
import commonCode

class Manage_logcal_db:
    """
    NOTE : 로컬 MS-SQL 관리 클래스
    DATE : 2021.04.26
    AUTH : JW
    """
    conn = ''
    cursor = ''

    def __init__(self, server, database, username, password, conntime=1800):
        """
        MS-SQL 관리 클래스 초기화
        :param server: 서버정보 (localhost\TOOD2008)
        :param database: 데이터베이스정보 WithpharmErp
        :param username: 접속ID
        :param password: 접속PW
        """
        self.server = server
        self.database = database
        self.username = "sa"
        self.password = "$dnlemvka3300$32!"
        self.re_conn_time = conntime

    def conn_open(self):
        """
        MS-SQL 커넥션 생성
        :return:
        """
        print("(로그) DB Connection 을 수행합니다.")
        print("(openDB) self.server :: ", self.server)
        print("(openDB) self.user :: ", self.username)
        print("(openDB) self.password :: ", self.password)
        print("(openDB) self.dbName :: ", self.database)
        print("(openDB) self.re_conn_time :: ", self.re_conn_time)
        try:
            self.conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + self.server + ';DATABASE=' + self.database + ';UID=' + self.username + ';PWD=' + self.password)
            self.cursor = self.conn.cursor()
            print("dbName:", self.database)
            print("(로그) DB Connection 수행을 완료하였습니다.")
        except BaseException as e:
            print('##### connection Error!! :: ', e)

            # TODO 23.10.24 connection error 시 오류내역을 API로 전달하고, 재귀 수행한다.
            print("## DB 연결을 재귀수행합니다.")
            sys.setrecursionlimit(1000)
            # sys.setrecursionlimit(10**5)

            # DB 연결 실패시 재연결 대기를 30분으로 조정
            # 대기상태의 setrecursionlimit 최대재귀깊이(횟수)가 넘을 것을 대비하여 재연결 대기는 30분으로 고정
            #
            time.sleep(float(self.re_conn_time))
            self.conn_open()

            return False
            # return traceback.format_exc()
            # commonMsg.alertMessage('내손안의약국', '로컬 DB 연결실패!\n관리자문의바랍니다.')
            # sys.exit("Local Database Not Connection")
        else:
            print("##### DB Connection Success")
            return True

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
            # commonMsg.alertMessage('내손안의약국', '로컬 DB 연결종료실패!\n관리자문의바랍니다.')
            # sys.exit("Local Database Close Failed")

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
        try:
            dataFrame = pd.read_sql_query(queryArr, self.conn)
        except pd.errors.DatabaseError as e:
            common_log = commonCode.commonLog('', '', '999999')
            err_msg = 'QUERY :: {} ERROR :: {}'.format(queryArr, traceback.format_exc())
            print("## sendAPI error msg :: {}".format(err_msg))
            common_log.send_api_log("ERR-001", err_msg)
            return False
        else:
            return dataFrame

    def send_query_update(self, queryMsg):
        """
        쿼리 발송 처리 (UPDATE 용 쿼리- pandas에서는 UPDATE 가 UPSERT 로 동작하는데, 유니크키가없으면 동작하지않으므로 별도제작)
        :param queryMsg:
        :return: 결과데이터를 pandas dataframe 처리하여 리턴
        """
        try:
            count = self.cursor.execute(queryMsg)
            print("## query count :: {}".format(self.cursor.rowcount))
        except BaseException as e:
            print("(에러) sendQuery 중 오류가 발생하였습니다.", e)
            print(traceback.format_exc())
            self.conn.rollback()
            return 'DB_SEND_QUERY_ERROR'
        else:
            self.conn.commit()
            return self.cursor.rowcount

    def send_query_prelink_insert(self, dataArray):
        """
        처방전 최종연계결과 플래그적용 INSERT 쿼리를 전송합니다.
        :param queryArr: SQL String
        :return: 전송결과
        """
        try:
            count = self.cursor.execute("""INSERT INTO WithpharmDrx.dbo.DrxsPrescriptionLinkInfo (CusNo, UserId, PrescriptionCd, TransStatus, TransDt, AuthTableFlag) VALUES (?,?,?,?,GETDATE(),?)""", dataArray[0], dataArray[1], dataArray[2], dataArray[3], dataArray[5])
            self.conn.commit()
        except Exception as e:
            print("##### (send_query_insert) Error :: ", e)
            return False
        else:
            return True

    def update_ci_query(self, item):
        """
        CI 정보를 UPDATE 처리한다.
        :param item: 생성 쿼리 item 정보 (단골회원정보 dict)
        :return:
        """
        try:
            update_query = []
            update_query.append("UPDATE WithpharmDrx.dbo.DrxsCustomersAuth SET")
            update_query.append("UserSmsCi = '" + item['sms_ci'] + "'")
            update_query.append(", UserSmsCiDte = GETDATE()")
            update_query.append("WHERE 1=1")
            update_query.append("AND UserId = '" + item['idx'] + "'")
            update_query.append("AND UserSmsCi IS NULL OR UserSmsCi = ''")

            update_sql = " ".join(update_query)

            print("## (CI-UPDATE-SQL) :: {}".format(update_sql))

            count = self.cursor.execute(update_sql)
            self.conn.commit()
        except Exception as e:
            print("##### (UPDATE) Error :: ", e)
            print(traceback.format_exc())

    def delete_ci_query(self):
        """
        AUTH 테이블 내 공백 CI 필드 데이터를 삭제 처리한다.
        :return:
        """
        try:
            print("## WithpharmDrx.dbo.DrxsCustomersAuth CI 미존재 데이터 삭제 ")
            delete_query_list_ci = []
            delete_query_list_ci.append("DELETE FROM WithpharmDrx.dbo.DrxsCustomersAuth")
            delete_query_list_ci.append("WHERE 1=1")
            delete_query_list_ci.append("AND UserSmsCi = '' OR UserSmsCi IS NULL")

            delete_query_ci = " ".join(delete_query_list_ci)

            count = self.cursor.execute(delete_query_ci)
            self.conn.commit()

            print("## DrxsCustomersAuth1 공백 CI 데이터를 삭제 정리 프로세스 완료 ")
        except Exception as e:
            print("##### (UPDATE) Error :: ", e)
            print(traceback.format_exc())



    def send_query_authinfo_insert(self, dataArray):
        """
        신규연계회원의 연계플래그정보를 INSERT 처리한다.
        :param queryArr: SQL String
        :return: 전송결과
        """
        try:
            count = self.cursor.execute("""INSERT INTO WithpharmDrx.dbo.DrxsCustomersAuth (CusNo, UserId, CustomerAuthFlag, PharmAuthFlag, CustomerAuthDte) VALUES (?,?,?,'N',GETDATE())""", dataArray[0], dataArray[1], dataArray[2])
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
            count = self.cursor.execute("""UPDATE WithpharmDrx.dbo.DrxsCustomersAuth SET CustomerAuthFlag = ?, CustomerAuthDte = GETDATE() WHERE CusNo = ?""", dataArray[0], dataArray[1])
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
