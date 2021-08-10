import pymssql

# connection object
global conn


def connectionMssqlDb(server, database, username, password):
    """
    MS-SQL DB에 연결한다.
    :param server:      DB서버주소
    :param database:    데이터베이스 이름
    :param username:    접속유저명
    :param password:    접속유저패스워드
    :return:            connection Object
    """
    print('##### MS-SQL DB Connect')
    conn = pymssql.connect(server, username, password, database)
    cursor = conn.cursor()

    print('##### MS-SQL DB Connect Success !!')
    return conn, cursor


def connectionClose():
    """
    MS-SQL DB 연결을 종료한다.
    :return:
    """
    print('##### MS-SQL DB Disconnect')
    conn.close()
    print('##### MS-SQL DB Disconnect Success !!')

# Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     print('##### DB 커넥션 체크')
#     server = 'localhost\\tood2008'
#     # server = '127.0.0.1\\tood2008'
#     database = 'WithpharmErp'
#     username = 'sa'
#     password = '$dnlemvka3300$32!'
#
#     connectionMssqlDb(server, database, username, password)