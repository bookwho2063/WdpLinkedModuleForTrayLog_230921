# -*- coding: utf-8 -*-
"""
# TITLE : AES-256-CBC 방식 암,복호화 클래스
# DATE : 2022.10.13
# AUTH : JW
"""
import base64
import hashlib

from Cryptodome.Random import get_random_bytes
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad


class CustomCipher:
    def __init__(self):
        self.cipherKeys = "1T3J63ET8A9AE6Y3FFB2EK5AV28N0FCM2J4B4M4QA7M69L6WL3"
        self.cipherKeysLength = len(self.cipherKeys)
        #self.rot_ptr_set = 128
        #self.key = self.encoder_key[:24]
        #self.iv = bytes(self.key, 'utf-8')

    # /** 자체 암호화 */
    def encrypt(self, plainText):

        reversedText = plainText[::-1]
        reversedTextLength = len(reversedText)

        encryptedArray = []

        for idx in range(0, reversedTextLength):
            cipherKeyIndex = idx % self.cipherKeysLength
            cipherKey = self.cipherKeys[cipherKeyIndex]
            reversedChar = reversedText[idx]

            encryptedValue = ord(reversedChar) ^ ord(cipherKey)
            encryptedValue = (encryptedValue << 3 & 0xF8) | (encryptedValue >> 5 & 0x07)

            encryptedArray.append(encryptedValue)
        # for end

        encryptedText = base64.b64encode(bytes(encryptedArray))[::-1].decode()
        encryptedText = encryptedText.replace("+", "^")

        return encryptedText

    def encryptBytes(self, plainBytes):

        reversedBytes = plainBytes[::-1]
        reversedBytesLength = len(reversedBytes)

        encryptedArray = []

        for idx in range(0, reversedBytesLength):
            cipherKeyIndex = idx % self.cipherKeysLength
            cipherKey = self.cipherKeys[cipherKeyIndex]
            reversedByte = reversedBytes[idx]

            encryptedValue = reversedByte ^ ord(cipherKey)
            encryptedValue = (encryptedValue << 3 & 0xF8) | (encryptedValue >> 5 & 0x07)

            encryptedArray.append(encryptedValue)
        # for end

        encryptedText = base64.b64encode(bytes(encryptedArray))[::-1].decode()
        encryptedText = encryptedText.replace("+", "^")

        return encryptedText

    # /** 자체 복호화 */
    def decrypt(self, cipherText):

        reversedText = cipherText.replace("^", "+")[::-1]
        reversedText = base64.b64decode(reversedText)

        reversedTextLength = len(reversedText)

        decryptedArray = []

        for idx in range(0, reversedTextLength):
            cipherKeyIndex = idx % self.cipherKeysLength
            cipherKey = self.cipherKeys[cipherKeyIndex]
            reversedByte = reversedText[idx]

            decryptedValue = (reversedByte >> 3 & 0x1F) | (reversedByte << 5 & 0xE0)
            decryptedValue = decryptedValue ^ ord(cipherKey)
            #decryptedValue = struct.pack('<h', decryptedValue)

            decryptedArray.append(decryptedValue)
        # for end

        decryptedBytes = bytes(decryptedArray[::-1])

        return decryptedBytes

class AESCipher256:
    def __init__(self):
        self.cipherKeys = "PharmacyInMyHands"
        self.secretKey = hashlib.md5(self.cipherKeys.encode()).hexdigest().encode()
        self.blockSize = AES.block_size
        self.aesMode = AES.MODE_CBC

    def encrypt(self, plainBytes):
        iv = get_random_bytes(self.blockSize)
        cipher = AES.new(self.secretKey, self.aesMode, iv)
        #return base64.b64encode(iv + cipher.encrypt(pad(plainBytes, self.blockSize)))
        return iv + cipher.encrypt(pad(plainBytes, self.blockSize))

    def decrypt(self, cipherBytes):
        iv = cipherBytes[:self.blockSize]
        cipher = AES.new(self.secretKey, self.aesMode, iv)
        return unpad(cipher.decrypt(cipherBytes[self.blockSize:]), self.blockSize)

# main
# if __name__ == '__main__':
#     """
#     # key = md5()
#     # AES-256-CBC
#     # 자체 128 Enc
#     """
#
#     print('TESTING ENCRYPTION')
#     # msg = input('Message...: ')
#     # pwd = input('Password..: ')
#     #key = 'PharmacyInMyHands'
#     msg = 'ABCD'
#     #time = int(time())
#     #print("time :: ",time)
#
#     #md5_time = md5(str(time).encode('utf-8')).digest()
#     # md5 결과를 16진수로 바꾸고 32자리가 안될경우 앞을 경으로 채운다
#     #print("md5_time byte :: ", md5_time)
#     #print("md5_time byte to 16bit :: ", md5_time.hex())
#     #md5_time_hex = md5_time.hex()
#
#     #print("md5_time_hex len :: ", len(md5_time_hex))
#     #print("md5_time_hex type :: ", type(md5_time_hex))
#     #if len(md5_time_hex) < 32:
#     #    tt = md5_time_hex.zfill(32)
#         #print("tt : ", tt)
#
#     # key_md5 = md5(key.encode('utf8')).digest()
#     # key = md5(key.encode('utf8')).digest()
#     #print('key 텍스트:', key)
#     # print('key md5:', key_md5)
#
#     #enc128_data = AESCipher128().Encrypt128(msg)
#     #print('(최종)msg 암호화 된 코드:', enc128_data)
#
#     #dec128_data = AESCipher128().Decrypt128(enc128_data)
#     #print('복호화 msg된 코드 type :', dec128_data)
#
#     ###########
#     # 암호화 처리
#
#     #print('AES256 암호화 대상 텍스트:', msg)
#     # 시간(md5)+암호대상평문을 인자로
#     #enc_data = AESCipher256(key).encrypt(md5_time_hex+msg)
#     #print('AES256 암호화 된 코드:', enc_data)
#
#     #enc128_data = AESCipher128().Encrypt128(enc_data)
#     #print('(최종)AES128 암호화 된 코드:', enc128_data)
#
#     #sample
#     #enc128_datas = str("40OQv88B3yX2P2x7EcxZx8eyXz3J68WbtzguovhpK2kUgYY0lTMuHs9FjexC8KYGWSh5jpsDV65RZnEAXxoIcCNpki5r8LMGDNGsUoUA7j6qHGdPJCGZfLGwFVYXw51R0UzFq0wDYLvn4aYpoxpi^VzbTzxFEznGdhbDzBJwhrvp^oKgYgECz5GEurTGYjUHCwb5ksx2C3MZnvZkqvEn0tXhzidtR3F9miLlL7fYq8mU7Q99VH65tedzUIDKFnkpDktmhnvpes0kWcczff3ArrrFaIwr2EMFUMSy1jkyWPvyVKENzMZF6IJpFtVuBHSTSxwrkd7dUvtGMqVM9oT9jgqL/f6Ef0xuZGANexqriioT2FqOXCqvhBuFFLk/x75TvvNBz^Y/6BpR6h2gdj17POjqu58i8WAMi9qQnrehl7D2y4bbnomBzT4Pn9DKgvhs")
#
#     ###########
#     # 복호화 처리
#
#     #print("복호화 대상 코드 : ", enc128_datas)
#
#     #dec128_data = AESCipher128().Decrypt128(enc128_data)
#     #print('복호화 된 코드 type :', type(dec128_data))
#     #print(dec128_data)
#
#     #dec_data = AESCipher256(key).decrypt(dec128_data)
#     #print('복호화 된 텍스트:', dec_data[32:])
#
#     #=====================================================
#     milliseconds = str(int(time.time() * 1000))
#     prefix = hashlib.md5(milliseconds.encode()).digest()
#     plainText = 'IOJGYvdewqG2YGfG6ozwygNKbNfACPPW6nE45B08ADWSyO5mxHVKKjGSbGMqzEXuCEWSYNIwasOYbmycBmw06D2KTgkEgHMeBA2wApIAZK^6AkpYQI1oRD7K5pFE4hqGIE1EYE0uAgpYYEBUoK9YRNrEwrMYiAMAooAq6OSuaOcQ6gtuDu^^Agw2goS24NLYpNQU4rSS5Cr8BpwowsPKaiRkDjHwQkj2iCyGqExCLnkApGC2zLDgTMt4YvNqSBue7nTQ7FUOLDYeZJ8ATOIEDsoggH3iIs94rtiURn9K4on4os^gTMYOLOp2AuMUZF^I4ov2gG3ypAAKzOfSygk2IlkURJWGBJsCzrMiyMD8Qob6rtaK6kFMzk0wYLSYyjBAQpKG7OeMAMTc4IYYoCkARj3uxpFMbHBAyPH2CHrWaPf^SD6^Ci0sJuz6oj9iaGz44i4^jjiEaFeGjg5oSBTcIOAmyHJUgl3sxCp6iDpOggAOwChqBhEy7jHaYDT0qu4M4s1MLO\/ULDEEBEigJm2CgkYGSlEOpH1^YqdqoNIcBOfACoAGxiBo6uZMzBa2qEEC4N\/yjiTARBBYzKP0jOTExpy2IGlO5J4UYD1oTlIMQNDyAHHMaH1IoEw^aiEGxshwgNXSggP6gu7gKH1U7kYK7B5uTlHSruDQiEEKTHxaLELKSA024OOIbktY5p6IgJeGhDD87AkyoN7oTD3ShNoihmrY5lzshh3owEICgFMspKd^hIvkTOQIyqFowtOqbIYcCvKwSkjmYiG8jidiIgA8zKY4poCEIucSJhrgwNReAPfOglNWTiTA4AjGCCBsaHsoqG32hGzOzrduoMsy7jZAbAt2Dm9kiD0iLmNerBM0qEFWLMrsJC3WDA5CIM8kJF7AIonyxpJsBpTICjka5tLwZCPSIMAIhFg^zjq8hmHUIMkKxmpuJO^MgNqG4tAMKPNAboaaAscqbPYkSH^YQtcIqPx0gKQsiqRopBw2oOakBhhA4Kc44pbGIg94LJJ4AHNK4EOgDDx2yliATFxyrCy2YEk0QkboyGBeDlRiqnPoSDMozvBkrHbEqioc5vIWTHoO7gwyRlq8hD7w4PDuDMw4yj1sgMVuLinOQrvC4m0GIE4MRifAaF9kRFg4ZJwCwMN6IsxASMCcpuf^jNMKimX4rPsq4tTWyGAcINfubNF^AoJYpNaIzm24bJY4QoHMzFWaAvO4ium^7Hf2iE0G7hjw5i6GYJQkoA8mTjVEimzEjGJkaAUAggzahNCcriLGqBpa4E2WKHswpjDCgm54TPqczPAADIeoCg96IMSy7O427DHALno2IBLIYlZeDugMBC2CpN9OxB1MIsOCaJVshLT27pbGwt5MLHi64KJSTMRYrJAoAs^E5q^A4qzS4k5E5vPOAiwuAhJgoMScSjMY'
#     print('자체 평문:', plainText)
#     customDecryptedBytes = CustomCipher().decrypt(plainText)
#     print("##### 자체 복호화 결과 :: ", customDecryptedBytes, len(customDecryptedBytes))
#     aseDecryptedBytes = AESCipher256().decrypt(customDecryptedBytes)
#     dec_data = aseDecryptedBytes[len(prefix):].decode()
#     print('##### 최종 복호화 결과:', dec_data)
#     print('##### 최종 복호화 결과 type :', type(dec_data))
#
#     # cipherText = CustomCipher().encrypt(plainText)
#     # print('자체 암호화:', cipherText)
#     print('자체 복호화:', CustomCipher().decrypt(plainText).decode())
#
#     #=====================================================
#     print('AES 평문:', plainText)
#
#     cipherBytes = AESCipher256().encrypt(plainText.encode())
#     print('AES 암호화:', cipherBytes)
#     #print('AES 복호화:', AESCipher256().decrypt(base64.b64decode(cipherBytes)).decode())
#     print('AES 복호화:', AESCipher256().decrypt(cipherBytes).decode())
#
#
#     #=====================================================
#     print('PIP 평문:', plainText)
#     milliseconds = str(int(time.time() * 1000))
#     #prefix = hashlib.shake_128(milliseconds.encode()).digest(16)
#     prefix = hashlib.md5(milliseconds.encode()).digest()
#
#     aseEncryptedBytes = AESCipher256().encrypt(prefix + plainText.encode())
#     customEncryptedText = CustomCipher().encryptBytes(aseEncryptedBytes)
#     print('PIP 암호화:', customEncryptedText)
#
#     #customEncryptedText = "V7webv7tT2Pw9rSCUszGByDy^O5uziFC91ffTciYWDajZ^2ds8iH302q20DjaCYs"
#     # customEncryptedText = "zHNrasiH4O6fufjxabEi90D96dAFRyyGB61TomYn7WkKKl4KLFGdzqm4sUprQfgi"
#     customEncryptedText = "O0/DSm^JNcE9LwunyjbzP4Ijz90r03GoJoHoiLv3dMCpUuIEbFiH2jCUpDGQHFze"
#
#     customDecryptedBytes = CustomCipher().decrypt(customEncryptedText)
#     #aseDecryptedBytes = AESCipher256().decrypt(base64.b64decode(customDecryptedBytes))
#     aseDecryptedBytes = AESCipher256().decrypt(customDecryptedBytes)
#
#     #print("aseDecryptedBytes :: ", aseDecryptedBytes)
#     #f359d370104267f0Array
#     print('PIP 복호화:', aseDecryptedBytes[len(prefix):].decode())