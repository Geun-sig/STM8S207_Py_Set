import unittest
import sys
import os

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.serial_comm import nmea_parser


class TestNMEAParser(unittest.TestCase):
    """NMEA 파서 테스트"""

    def test_checksum_calculation(self):
        """체크섬 계산 테스트"""
        # 알려진 값으로 테스트
        sentence = "SC,18.5,13.2,1.25,12.0"
        checksum = nmea_parser.calculate_nmea_checksum(sentence)
        # 체크섬은 2자리 16진수여야 함
        self.assertEqual(len(checksum), 2)
        self.assertTrue(all(c in '0123456789ABCDEF' for c in checksum))

    def test_validate_sentence_valid(self):
        """유효한 NMEA 문장 검증 테스트"""
        # 실제 체크섬 계산
        data = "SC,18.5,13.2,1.25,12.0"
        checksum = nmea_parser.calculate_nmea_checksum(data)
        sentence = f"${data}*{checksum}\r\n"

        self.assertTrue(nmea_parser.validate_nmea_sentence(sentence))

    def test_validate_sentence_invalid(self):
        """잘못된 체크섬 테스트"""
        sentence = "$SC,18.5,13.2,1.25,12.0*FF\r\n"
        self.assertFalse(nmea_parser.validate_nmea_sentence(sentence))

    def test_parse_sc_data_valid(self):
        """$SC 데이터 파싱 테스트"""
        # 유효한 문장 생성
        data = "SC,18.5,13.2,1.25,12.0"
        checksum = nmea_parser.calculate_nmea_checksum(data)
        sentence = f"${data}*{checksum}\r\n"

        result = nmea_parser.parse_sc_data(sentence)

        self.assertIsNotNone(result)
        self.assertEqual(result.solar_voltage, 18.5)
        self.assertEqual(result.battery_voltage, 13.2)
        self.assertEqual(result.current, 1.25)
        self.assertEqual(result.output_voltage, 12.0)

    def test_parse_sc_data_invalid(self):
        """잘못된 $SC 데이터 파싱 테스트"""
        sentence = "$SC,invalid,data*FF\r\n"
        result = nmea_parser.parse_sc_data(sentence)
        self.assertIsNone(result)

    def test_parse_version_valid(self):
        """$LISTV 버전 파싱 테스트"""
        # 유효한 문장 생성
        data = "LISTV,A,B,C,D"
        checksum = nmea_parser.calculate_nmea_checksum(data)
        sentence = f"${data}*{checksum}\r\n"

        result = nmea_parser.parse_version(sentence)

        self.assertIsNotNone(result)
        self.assertEqual(result.version, ("A", "B", "C", "D"))
        self.assertEqual(str(result), "vA.B.C.D")

    def test_create_command(self):
        """명령 생성 테스트"""
        command = nmea_parser.create_command("LICMD,A")

        # $로 시작하고 *와 \r\n으로 끝나야 함
        self.assertTrue(command.startswith("$"))
        self.assertTrue("*" in command)
        self.assertTrue(command.endswith("\r\n"))

        # 생성된 명령의 체크섬이 유효해야 함
        self.assertTrue(nmea_parser.validate_nmea_sentence(command))

    def test_create_command_licmd(self):
        """LICMD 명령 생성 및 검증"""
        command = nmea_parser.create_command("LICMD,A")

        # 예상되는 명령 확인
        expected_checksum = nmea_parser.calculate_nmea_checksum("LICMD,A")
        expected = f"$LICMD,A*{expected_checksum}\r\n"

        self.assertEqual(command, expected)

    def test_negative_current(self):
        """음수 전류 파싱 테스트 (방전)"""
        data = "SC,18.5,12.8,-0.75,12.0"
        checksum = nmea_parser.calculate_nmea_checksum(data)
        sentence = f"${data}*{checksum}\r\n"

        result = nmea_parser.parse_sc_data(sentence)

        self.assertIsNotNone(result)
        self.assertEqual(result.current, -0.75)


if __name__ == '__main__':
    # 테스트 실행
    unittest.main()
