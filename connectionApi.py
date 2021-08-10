# -*- coding: utf-8 -*-
#!/usr/bin/python

import requests

class api_manager:

    def __init__(self):
        pass

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
        except requests.exceptions as e:
            print("##### 내손안의약국 API 서버 연결실패\n관리자문의바랍니다.!!")
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
            return dictKeys, jsonDic
        except requests.exceptions as e:
            print('##### api_conn error\n', e)

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
            print("##### (api_send_post) url :: ", url)
            print("##### (api_send_post) datas :: ", datas)

            # response = requests.post(url, json=datas)     # json 타입으로 보내면 이스케이프문자 \ 가 들어가서 서버에서 파싱이 안된다고 하심
            response = requests.post(url, data=datas)       # 일반 타입으로 보냄
            print("##### (response.status_code) response.request :: ", response.request)
            print("##### (response.status_code) response :: ", response.text)
            print("##### (response.status_code) response.status_code :: ", response.status_code)
            if response.status_code != 200:
                print("##### (api_send_get) API CODE ERROR :: ", response.status_code)

            print("##### (api_send_post) response :: ", response.json())
            dictData = response.json()
            dictKey = dictData.keys()
            return dictKey, dictData
        except Exception as e:
            print("##### api_conn_post error\n", e)


# if __name__ == '__main__':
#     print('##### connecti자사on Api')
#
#     # url = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList?serviceKey=7Aka%2Fpt6e5ojk4k%2FmNbgQqGGCzQ8HG7betsaPcL0PNXKzzTdqeb8e6UlYjVnNTYr%2BISwXkN4C1L5kkmCQLq8ow%3D%3D&pageNo=1&numOfRows=3&itemName=%ED%95%9C%EB%AF%B8%EC%95%84%EC%8A%A4%ED%94%BC%EB%A6%B0%EC%9E%A5%EC%9A%A9%EC%A0%95100%EB%B0%80%EB%A6%AC%EA%B7%B8%EB%9E%A8&type=json"
#     url = "https://72064269-76a7-4d86-b7d9-913ed54e8829.mock.pstmn.io/authCheck?PharmNm=%EA%B0%95%EC%A7%84%EC%95%BD%EA%B5%AD&PharmNo=00011110&SaupNo=3333333333&PharmType=WP"
#     html = requests.get(url)
#     print(html.text)
#     print('----------------------------------------------------------')
#     print('----------------------------------------------------------')
#
#     # 딕셔너리 형태로 파싱
#     jsonDic = html.json()
#     print(jsonDic)
#     print(jsonDic['Status'])
#
#     # 키 출력
#     dictKeys = jsonDic.keys()
#     print(dictKeys)


