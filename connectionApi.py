# -*- coding: utf-8 -*-
#!/usr/bin/python
import json
import traceback

import requests, urllib3

import commonCode
import common_process

class api_manager:

    def __init__(self):
        self.common_class = commonCode.commonCode()

    def api_conn_check(self, url):
        """
        api 서버 커넥션 체크
        :param url:
        :return: 체크결과 boolean
        """
        try:
            html = requests.get(url)
            print("##### api call Check Return html :: ", html)

            jsonDic = html.json()
            print("##### api call Check Return htmlToJson :: ", jsonDic)

            if jsonDic['Status'] == 'ok':
                return "OK"
            elif jsonDic['Status'] == 'error':
                return "NO_USER"
        except requests.exceptions.Timeout as e:
            # commonMsg.alertMessage('내손안의약국', 'API 연결 실패!\n관리자 문의 및 원격지원요청바랍니다.(TIME_OUT)')
            print("#####(타임아웃2) 내손안의약국 API 서버 연결실패\n관리자문의바랍니다.!!")
            print(traceback.format_exc())
            # 로그 발송 처리
            # self.common_class.send_api_log(organ_number='', biz_number='', pharmacy_idx='', err_code='ERR-002', err_msg='DB_CONNECTION_TIME_OUT')
            return False
        except requests.exceptions.ConnectTimeout as e:
            # commonMsg.alertMessage('내손안의약국', 'API 연결 실패!\n관리자 문의 및 원격지원요청바랍니다.(CONNECTION_TIME_OUT)')
            print("#####(타임아웃) 내손안의약국 API 서버 연결실패\n관리자문의바랍니다.!!")
            print(traceback.format_exc())
            # self.common_class.send_api_log(organ_number='', biz_number='', pharmacy_idx='', err_code='ERR-002', err_msg='DB_CONNECTION_TIME_OUT')
            return False
        except requests.exceptions.ConnectionError as e:
            # commonMsg.alertMessage('내손안의약국', 'API 연결 실패!\n관리자 문의 및 원격지원요청바랍니다.(CONNECTION_ERROR)')
            print("#####(커넥션에러) 내손안의약국 API 서버 연결실패\n관리자문의바랍니다.!!")
            print(traceback.format_exc())
            # self.common_class.send_api_log(organ_number='', biz_number='', pharmacy_idx='', err_code='ERR-002', err_msg='DB_CONNECTION_TIME_OUT')
            return False

    def api_conn(self, url):
        """
        api 전송 후 결과를 JSON 키리스트 / 딕셔너리 형태로 변환하여 리턴한다 (GET 방식)
        :param url:
        :return: keys, Dict
        """
        try:
            print("##### api_conn url :: ", url)
            result = requests.get(url)
            jsonDic = result.json()
            dictKeys = jsonDic.keys()
        except requests.exceptions as e:
            print('##### api_conn error\n', e)
            print(traceback.format_exc())
            return False, traceback.format_exc()
        except BaseException as be:
            print(traceback.format_exc())
            return False, traceback.format_exc()
        else:
            return dictKeys, jsonDic

    def api_send_get(self, url, datas):
        """
        API를 GET 방식으로 전송하고 결과를 딕셔너리로 반환한다
        :param url: API 주소
        :param datas: 데이터 JSON
        :return: dictKey, dictData
        """
        try:
            print("##### (api_send_get) url :: ", url)
            print("##### (api_send_get) datas :: ", datas)
            response = requests.get(url, params=datas)
            if response.status_code != 200:
                print("##### (api_send_get) API CODE ERROR :: ", response.status_code)

            print("##### (api_send_get) response :: ", response.json())
            dictData = response.json()
            dictKey = dictData.keys()
            return dictKey, dictData
        except Exception as e:
        #except requests.exceptions as e:
            print("##### api_send_get error\n", e)

    def api_conn_post(self, url, datas):
        """
        POST 방식으로 API를 전달한 뒤 결과를 딕셔너리 형태로 변환하여 리턴한다.
        :param url: API URL
        :param datas: POST 인자 JSON 인자
        :return: 결과 딕셔너리
        """
        try:
            print("##### (API 발송 URL) :: ", url)
            print("##### (API 발송 데이터정보) :: ", datas)

            # TODO 230922 : 전달데이터 암호화 처리 후 전송
            enc_datas = common_process.common_process().proc_pip_encrypt(datas)
            send_data_dict = dict()
            send_data_dict['drxs'] = enc_datas

            print("## POST API 발송전 확인 :: {}".format(send_data_dict))
            print("## POST API 발송전 확인 json.dumps :: {}".format(json.dumps(send_data_dict)))

            # response = requests.post(url, json=datas)     # json 타입으로 보내면 이스케이프문자 \ 가 들어가서 서버에서 파싱이 안된다고 하심
            response = requests.post(url, data=json.dumps(send_data_dict))       # 일반 타입으로 보냄
            print("##### (API 발송 리턴 정보) response :: ", response.text)
            print("##### (API 발송 리턴 정보) response.status_code :: ", response.status_code)
            if response.status_code != 200:
                print("##### (api_send_get) API CODE ERROR :: ", response.status_code)
                return False, traceback.format_exc()

            # TODO 230922 : 데이터 전송 결과정보 복호화 후 JSON 리턴
            print("##### (api_send_post_ENCRYP) response :: ", response.json())
            enc_result_datas = response.json()
            dec_datas = common_process.common_process().proc_pip_decrypt(enc_result_datas['drxs'])

            print("##### (api_send_post_DECRYP) response :: ", response.json())
            print("##### (api_send_post_DECRYP) dec_datas :: ", dec_datas)
            print("##### (api_send_post_DECRYP) type(dec_datas) :: ", type(dec_datas))

            dictData = json.loads(dec_datas)
            print("##### type(dictData) :: ", type(dictData))
            print("##### dictData :: ", dictData)
            dictKey = dictData.keys()
            print("##### dictKey :: ", dictKey)

        except urllib3.exceptions.MaxRetryError:
            print("urllib3.exceptions.MaxRetryError")
            print(traceback.format_exc())
            return False, traceback.format_exc()
        except ConnectionRefusedError:
            print("서버에 연결할 수 없습니다.")
            print("서버의 IP/PORT 정보를 확인하세요")
            print("서버실행여부 및 서버의 보안정책을 확인하세요")
            return False, traceback.format_exc()
        except requests.ConnectionError:
            print("requests.ConnectionError")
            print(traceback.format_exc())
            return False, traceback.format_exc()
        except requests.Timeout:
            print("requests.Timeout")
            print(traceback.format_exc())
            return False, traceback.format_exc()
        except requests.ConnectTimeout:
            print("requests.ConnectTimeout")
            print(traceback.format_exc())
            return False, traceback.format_exc()
        else:
            return dictKey, dictData


# if __name__ == '__main__':
#     print('##### connecti자사on Api')
#     apiMng = api_manager()

    # 모듈상태 API
    # datas = dict()
    # datas['PHARMACY_IDX'] = '38'
    # datas['STATUS'] = 'R'
    # params = json.dumps(datas)
    # url = 'https://dev-wp-api.drxsolution.co.kr/setModuleTransState.drx'

    # 오류로그정보전송
    # datas = dict()
    # datas['PHARMACY_IDX'] = '38'
    # datas['ERR_TYPE'] = 'ERROR_TEST'
    # datas['DESCRIPTION'] = '에러내역 테스트 전송'
    # params = json.dumps(datas)
    # url = 'https://dev-wp-api.drxsolution.co.kr/setProcessTransError.drx'

    # 동명이인정보 전송
    # datas = dict()
    # datas['MEMBER_IDX'] = '138'
    # datas['PHARMACY_IDX'] = '38'
    # datas['USER_NAME'] = '박준욱'
    # datas['MOBILE'] = '01028501492'
    # datas['BIRTH'] = '870310'
    # datas['SEX'] = 'M'
    # datas['SW_TYPE'] = 'WDP'
    # datas['DATA_COUNT'] = '2'
    #
    # items = list()
    # for idx in range(1, 3):
    #     item = dict()
    #     item['CusNo'] = 'C000000' + str(idx)
    #     item['FamNo'] = '박아빠'
    #     item['CusNm'] = '박준욱'
    #     item['CusJmno'] = 'kasjhdghfauiyweskjdfhk'
    #     item['RealBirth'] = '870310'
    #     item['Sex'] = 'M'
    #     item['CertiNo'] = '1234567890' + str(idx)
    #
    #     print("#### item :: ", item)
    #     items.append(item)
    #
    # datas['ITEMS'] = items
    # params = json.dumps(datas)
    # url = 'https://dev-wp-api.drxsolution.co.kr/setMemberPharmacySameName.drx'

    # 1,2차 단골회원정보 내손 전송
    # datas = dict()
    # datas['MEMBER_IDX'] = '138'
    # datas['PHARMACY_IDX'] = '38'
    #
    # items = list()
    # for idx in range(1, 3):
    #     item = dict()
    #     item['MEMBER_IDX'] = str(137 + idx)
    #     item['CusNo'] = 'C000000' + str(idx)
    #     item['FamNo'] = '박아빠'
    #     item['CusNm'] = '박준욱' + str(idx)
    #     item['CusJmno'] = 'kasjhdghfauiyweskjdfhk'
    #     item['RealBirth'] = '870310'
    #     item['Sex'] = 'M'
    #     item['CertiNo'] = '1234567890' + str(idx)
    #
    #     print("#### item :: ", item)
    #     items.append(item)
    #
    # datas['ITEMS'] = items
    # params = json.dumps(datas)
    # url = 'https://dev-wp-api.drxsolution.co.kr/setMemberPharmacyLinkStateUpdate.drx'


    # 검증완료 동명이인 정보 요청
    # datas = dict()
    # datas['PHARMACY_IDX'] = '38'
    # params = json.dumps(datas)
    # url = 'https://dev-wp-api.drxsolution.co.kr/getMemberPharmacySameNameChoice.drx'
    #
    # returnKey, returnValuse = apiMng.api_conn_post(url, params)
    #
    # print("#####(returnKey) :: ", returnKey)
    # print("#####(returnValuse) :: ", returnValuse)





































