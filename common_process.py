# -*- coding: utf-8 -*-
"""
# TITLE : 공통 프로세스 작업 클래스
# DATE : 2022.10.13
# AUTH : JW
"""
import json
import traceback

import common_crypt_leedm
import time
import hashlib

class common_process:
    """
    TITLE : 공통처리함수 클래스
    DATE : 230125
    """

    def __init__(self):
        pass

    def proc_pip_encrypt(self, plain_json_text):
        """
        내손안의약국으로 전달할 json 데이터 str을 내부 암호화 후 리턴한다.
        :param plain_json_text:
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

    def proc_pip_decrypt_image(self, enc_datas):
        """
        내손안의약국에서 전달받은 json 데이터중 처방전(바이트이미지)을 복호화 한다
        :param enc_datas:
        :return: 복호화 결과 byte 이미지 데이터
        """
        try:
            milliseconds = str(int(time.time() * 1000))
            prefix = hashlib.md5(milliseconds.encode()).digest()

            customDecryptedBytes = common_crypt_leedm.CustomCipher().decrypt(enc_datas)

            aseDecryptedBytes = common_crypt_leedm.AESCipher256().decrypt(customDecryptedBytes)
            dec_data = aseDecryptedBytes[len(prefix):]
            # print("복호화 이미지 dec_data :: {}".format(dec_data))
        except Exception as e:
            print('##### (proc_pip_decrypt_image) Error : ', e)
            print(traceback.format_exc())
            return 'ERROR_PIP_DECRYPT'
        else:
            return dec_data

    def proc_pip_decrypt_inner_jmno(self, enc_datas):
        """
        내손안의약국에서 전달받은 암호화 주민번호를 복호화 처리하여 리턴
        :param enc_datas:
        :return: 복호화 결과 str
        """
        try:
            milliseconds = str(int(time.time() * 1000))
            prefix = hashlib.md5(milliseconds.encode()).digest()

            print("##### 복호화 대상 주민번호 :: ", enc_datas)

            customDecryptedBytes = common_crypt_leedm.CustomCipher().decrypt(enc_datas)
            print("##### 자체 복호화 주민번호 결과 :: ", customDecryptedBytes, len(customDecryptedBytes))
        except Exception as e:
            print('##### (proc_pip_decrypt) Error : ', e)
            return 'ERROR_PIP_DECRYPT'
        else:
            return customDecryptedBytes.decode('utf-8')



    def proc_receive_data_check(self, recv_data_json):
        """
        전송된 데이터의 실패 또는 에러체크
        :param recv_data_json: 전송된 데이터
        :return: 리턴코드 및 에러코드 (성공시 에러코드는 공백)
        """
        try:
            # ERROR 상태 체크
            # if recv_data_json['member-idx'] == '':
            #     print("##### BSW100 : 내부 쿼리가 오류인 경우 (result : ERROR)")
            #     return "ERROR", "BSW100"
            # elif recv_data_json['member-idx'] == '':
            #     print("##### BSW101 : 기타 (result : ERROR)")
            #     return "ERROR", "BSW101"

            # FAILED 상태 체크
            if recv_data_json['member-idx'] == '':
                print("##### BSW102 : 회원 고유키값 전송 데이터가 없는 경우 (result : FAILED)")
                return "FAILED", "BSW102"
            elif recv_data_json['member-name'] == '':
                print("##### BSW103 : 회원 이름 전송 데이터가 없는 경우 (result : FAILED)")
                return "FAILED", "BSW103"
            elif recv_data_json['member-jumin'] == '':
                print("##### BSW104 : 회원 주민번호(암호화된) 전송 데이터가 없는 경우 (result : FAILED)")
                return "FAILED", "BSW104"
            elif recv_data_json['member-mobile'] == '':
                print("##### BSW105 : 회원 휴대폰번호 전송 데이터가 없는 경우 (result : FAILED)")
                return "FAILED", "BSW105"
            elif recv_data_json['member-email'] == '':
                print("##### BSW106 : 회원 이메일 전송 데이터가 없는 경우 (result : FAILED)")
                return "FAILED", "BSW106"
            elif recv_data_json['member-sms-ci'] == '':
                print("##### BSW107 : 회원 SMS CI 전송 데이터가 없는 경우 (result : FAILED)")
                return "FAILED", "BSW107"
            # elif recv_data_json['member-idx'] == '':
            #     print("##### BSW108 : 기타 (result : FAILED)")
            #     return "FAILED", "BSW108"

        except Exception as e:
            return "ERROR"
        else:
            print("##### (전달받은 데이터 정합성체크) SUCCESS")
            return "SUCCESS", ""

    def proc_return_json_func(self, result_code, res_data, err_code):
        """
        리턴용 json 데이터 설정
        :param result_code: SUCCESS, FAILED, ERROR
        :param res_data:
        :param err_code:
            # 사용
            BSW100 : 내부 쿼리가 오류인 경우 (result : ERROR)
            BSW101 : 기타 (result : ERROR)
                BSW102 : DB NOT Connection (result : ERROR)

            # 사용
            BSW109 : 약국DB내 해당 회원 정보가 존재하지 않음. (result : FAILED)

            # 보류 ## (jmno_auth_check) 주민번호 복호화 관련 오류코드
            # BSW102 : 회원 고유키값 전송 데이터가 없는 경우 (result : FAILED)
            # BSW103 : 회원 이름 전송 데이터가 없는 경우 (result : FAILED)
            # BSW104 : 회원 주민번호(암호화된) 전송 데이터가 없는 경우 (result : FAILED)
            # BSW105 : 회원 휴대폰번호 전송 데이터가 없는 경우 (result : FAILED)
            # BSW106 : 회원 이메일 전송 데이터가 없는 경우 (result : FAILED)
            # BSW107 : 회원 SMS CI 전송 데이터가 없는 경우 (result : FAILED)
            # BSW108 : 기타 (result : FAILED)

            ## (receive_prescription_qr_info) QR 코드 인증 관련오류코드
            # BSW100 : 내부 쿼리 오류 (QR 복호화 후 처방전 INSERT 시 쿼리오류)
            # BSW101 : 내부 기타 오류 (쿼리오류 외 내부오류)
            # BSW102 : QR 스트링 미 존재 (receive key error)
            # BSW103 : qr-num 미 존재 (receive key error)
            # BSW104 : sms-ci 미 존재 (receive key error)
            # BSW105 : license-str 미 존재 (receive key error)
            # BSW106 : qrcode-idx 미 존재 (receive key error)
                # BSW107 : DB Connection Error
                # BSW108 : 처방환자정보 INSERT 오류
                # BSW109 : 약정보 INSERT 오류
                # BSW110 : 주사정보 INSERT 오류
                # BSW111 : member-idx 미 존재
                    # BSW112 : 처방전 이미지 복호화 오류
                    # BSW113 : 처방전 이미지 미존재

            ## (receive_prescription_payment_info) 결제정보 관련 오류코드
            #   PAY100 : DB Connection Error
            #   PAY101 : DB QUERY ERROR
            #   PAY102 : 업데이트 인자정보 불일치(업데이트 행 갯수 0)
            #   PAY103 : 기타오류 (내부오류)

            # [크레소티 복호화 오류]
            # CRE100 : 복호화서비스 미 가입 약국회원 (pharmacy-organ-num 으로 사용인증 안됨) / 사용기간 만료
            # CRE101 : 처방전 복호화 오류
                # CRE102 : 해당 처방전의 환자정보와 내손안의약국 회원정보와 다름

            # [이디비 복호화 오류]
            # EDB100 : 복호화서비스 미 가입 약국회원 (pharmacy-organ-num 으로 사용인증 안됨) / 사용기간 만료
            # EDB101 : 처방전 복호화 오류
                # EDB102 : 해당 처방전의 환자정보와 내손안의약국 회원정보와 다름

            # [유비케어 복호화 오류]
            # UBI100 : 복호화서비스 미 가입 약국회원 (pharmacy-organ-num 으로 사용인증 안됨) / 사용기간 만료
            # UBI101 : 처방전 복호화 오류
                # UBI102 : 해당 처방전의 환자정보와 내손안의약국 회원정보와 다름

        :return: dict 데이터 리턴
        """
        try:
            info_dict = dict()
            info_dict['result'] = result_code
            info_dict['res_data'] = res_data
            info_dict['err_code'] = err_code
        except Exception as e:
            print('##### (proc_jmno_auth_query_func) Error : ', e)
            return 'ERROR_CREATE_RETURN_JSON'
        else:
            return info_dict

    def proc_packing_drxs(self, packing_enc_data):
        """
        최종 전달할 암호데이터를 {"drxs":"암호문"} JSON 형태로 패킹 후 리턴한다.
        :param packing_enc_data: 전송할 암호문 스트링
        :return: 패킹결과 json
        """
        try:
            pack_dict = dict()
            pack_dict['drxs'] = packing_enc_data
        except Exception as e:
            print('##### (proc_packing_drxs) Error : ', e)
            return 'ERROR_JSON_PACKING'
        else:
            return json.dumps(pack_dict)

    def proc_error_return_func(self, type, content, err_code):
        """
        DB 오류로 인하여 에러 리턴시 데이터 생성 함수
        :return:
        """
        try:
            print("##### (결과정보) 리턴데이터 생성")
            print("## TYPE : {}\n## CONTENT : {}\n## ERR_CODE : {}".format(type, content, err_code))
            print("##########################")

            res_dict = dict()
            res_dict = self.proc_return_json_func(type, content, err_code)
            err_data_json = json.dumps(res_dict)

            enc_err_data = self.proc_pip_encrypt(err_data_json)
            err_send_data = self.proc_packing_drxs(enc_err_data)
        except Exception as e:
            print('##### (proc_error_return_func) Error : ', e)
            return 'ERROR_RETURN_PACKING'
        else:
            return err_send_data



# if __name__ == '__main__':
#     # sample_dict = dict()
#     # sample_dict['drxs'] = 'skjdfhalkshgkashglkjafhgkjahsdfgkjhsalkjflkjasdhfkjahsfkjhaskjdfhksaldhflkjashdfkj'
#     # send_data_json = json.dumps(sample_dict)
#     #
#     # cancel_data_api = "https://drv-api.drxsolution.co.kr"
#     # post_headers = {'Content-Type': 'application/json', 'charset': 'utf-8', 'X-API-TYPE': 'setUserPrescriptionWeekReceptionInit'}
#     # response_api = requests.post(cancel_data_api, data=send_data_json, headers=post_headers)
#     #
#     # print("##### response info")
#     # print("status :: {}".format(response_api.status_code))
#     # print("content :: {}".format(response_api.content))
#     # print("headers :: {}".format(response_api.headers))
#     # print("url :: {}".format(response_api.url))
#     # print("text :: {}".format(response_api.text))


