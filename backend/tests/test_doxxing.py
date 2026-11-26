"""Tests for the pattern-based Doxxing detector (Section 6).

Every identifier below is invented for the test. The negative cases are ordinary chat
text, dates, amounts and IDs that a naive digit regex would wrongly flag; they matter as
much as the positives, because a false Doxxing flag raises severity (interfaces.md, Q4).
"""
import json
import time

import pytest

from app.services.custody_payload import canonical_json
from app.services.doxxing import (
    MATCH_TYPES, IdentifierMatch, detect_doxxing, find_identifiers,
)


def types(text):
    return detect_doxxing(text)["match_types"]


# --------------------------------------------------------------------------- contract
class TestContract:
    def test_shape_matches_interfaces_doc(self):
        result = detect_doxxing("call me on 0300-1234567")
        assert set(result) == {"detected", "match_types"}
        assert result == {"detected": True, "match_types": ["phone_number"]}

    @pytest.mark.parametrize("text", [None, "", "   \n\t "])
    def test_empty_input(self, text):
        assert detect_doxxing(text) == {"detected": False, "match_types": []}

    def test_non_string_rejected(self):
        with pytest.raises(TypeError):
            detect_doxxing(b"0300-1234567")

    def test_neutral_text(self):
        assert detect_doxxing("tum bohat bure ho, mujhse baat mat karna") == {
            "detected": False, "match_types": [],
        }

    def test_fixed_order_and_no_duplicates(self):
        text = (
            "Address: House No. 12, Street 5, G-9/2. Email ali.khan@example.com, "
            "CNIC 35202-1234567-1, numbers 0300-1234567 and 0321 7654321, "
            "backup bob@example.org"
        )
        assert types(text) == list(MATCH_TYPES)

    def test_result_never_contains_values(self):
        secrets = ["0300-1234567", "35202-1234567-1", "ali.khan@example.com", "12"]
        text = f"{secrets[0]} {secrets[1]} {secrets[2]} house no {secrets[3]} street 4"
        blob = json.dumps(detect_doxxing(text)) + repr(find_identifiers(text))
        for value in secrets[:3]:
            assert value not in blob
        assert "1234567" not in blob and "example" not in blob

    def test_canonical_json_is_stable(self):
        text = "0300-1234567 ali@example.com"
        assert canonical_json(detect_doxxing(text)) == canonical_json(detect_doxxing(text))

    def test_spans_point_into_input(self):
        text = "mera number 0300-1234567 hai"
        (m,) = find_identifiers(text)
        assert isinstance(m, IdentifierMatch)
        assert m.match_type == "phone_number"
        assert text[m.start:m.end] == "0300-1234567"


# ------------------------------------------------------------------------------ phone
class TestPhone:
    @pytest.mark.parametrize("text", [
        "0300-1234567",
        "03001234567",
        "0300 1234567",
        "0300 123 4567",
        "+92 300 1234567",
        "+923001234567",
        "+92-300-1234567",
        "0092 300 1234567",
        "923001234567",
        "(0300) 1234567",
        "iska number 0333.1234567 hai, sab call karo",
        "landline 042-35761234",
        "(021) 3456 7890",
        "051-1234567",
        "+92 51 1234567",
        "+44 20 7946 0958",
        "+1 415 555 0134",
        "number: ۰۳۰۰۱۲۳۴۵۶۷",
        "number: ٠٣٠٠١٢٣٤٥٦٧",
    ])
    def test_detected(self, text):
        assert types(text) == ["phone_number"], text

    @pytest.mark.parametrize("text", [
        "meeting on 2026-11-09 at 10:30",
        "date 09/11/2026",
        "Rs. 1,500,000 transfer kar do",
        "order id 123456789",
        "OTP 482913",
        "0300",
        "0300-12345",
        "3001234567",
        "version 1.2.3.4",
        "score 92 out of 100",
    ])
    def test_not_detected(self, text):
        assert "phone_number" not in types(text), text


# ------------------------------------------------------------------------------- CNIC
class TestCnic:
    @pytest.mark.parametrize("text", [
        "35202-1234567-1",
        "CNIC: 42101 1234567 3",
        "61101.1234567.9",
        "cnic 3520212345671",
        "iska shanakhti card number 3520212345671 hai",
        "شناختی کارڈ ۳۵۲۰۲۱۲۳۴۵۶۷۱",
    ])
    def test_detected(self, text):
        assert types(text) == ["cnic"], text

    @pytest.mark.parametrize("text", [
        "account 3520212345671",           # bare 13 digits without a CNIC keyword
        "95202-1234567-1",                 # first digit outside the province codes 1-7
        "35202-123456-1",                  # wrong group length
    ])
    def test_not_detected(self, text):
        assert "cnic" not in types(text), text

    def test_cnic_digits_not_also_phone(self):
        assert types("35202-1234567-1") == ["cnic"]


# ------------------------------------------------------------------------------ email
class TestEmail:
    @pytest.mark.parametrize("text", [
        "ali.khan@example.com",
        "mail karo: sara_99+fyp@uni.edu.pk",
        "ali @ gmail.com",
        "ali (at) gmail (dot) com",
        "ali[at]example[dot]org",
        "ali at gmail dot com",
        "ali at yahoo.com",
    ])
    def test_detected(self, text):
        assert types(text) == ["email"], text

    @pytest.mark.parametrize("text", [
        "meet me at the mall",
        "@ali tum kahan ho",
        "see you at 5. com on",
        "price is 5.com",
    ])
    def test_not_detected(self, text):
        assert "email" not in types(text), text

    def test_phone_inside_email_is_email_only(self):
        assert types("03001234567@gmail.com") == ["email"]


# ---------------------------------------------------------------------------- address
class TestAddress:
    @pytest.mark.parametrize("text", [
        "House No. 12, Street 5, G-9/2, Islamabad",
        "house # 45 block C",
        "H# 221-B",
        "H.No 7 Gulberg",
        "flat no 3B",
        "plot number 88",
        "makan number 14, gali 3",
        "ghar no. 9 mohalla qasimabad",
        "House 12, Street 5",                  # two weak components
        "Street 7, Block 13",
        "DHA Phase 5, Block H",
        "sector G-11/3, street 22",
        "Address: 15 Model Colony",
        "مکان نمبر ۱۲ گلی نمبر ۴",
        "گلی نمبر 4، محلہ اسلام پورہ",
    ])
    def test_detected(self, text):
        assert "address" in types(text), text

    @pytest.mark.parametrize("text", [
        "I went to his house 3 times",
        "ghar 2 baje aa jana",
        "block a user if they bother you",
        "street fight dekhi aaj",
        "phase 2 of the project is late",
        "mujhe nahi pata",
        "email address: not given",
        "the road 2 hours long",
        "we live in a colony of ants",
    ])
    def test_not_detected(self, text):
        assert "address" not in types(text), text


# ------------------------------------------------------------------------- realistic
class TestRealistic:
    def test_threatening_message_with_identifiers(self):
        text = (
            "Sab ko bata dunga, iska number 0312-9876543 hai aur ghar ka pata: "
            "House No 21, Street 9, F-8/1. Sab log jao wahan"
        )
        assert detect_doxxing(text) == {
            "detected": True, "match_types": ["phone_number", "address"],
        }

    def test_multiline_ocr_text(self):
        text = "Ali Khan\nonline\n\nyeh lo uski id\n42101-7654321-5\nab dekhna"
        assert types(text) == ["cnic"]

    def test_plain_harassment_not_flagged(self):
        text = (
            "Tum pagal ho, tumhe koi pasand nahi karta. 10 baar bola hai message mat karo. "
            "Kal 3 baje college ke bahar milna, 2026-11-10."
        )
        assert detect_doxxing(text)["detected"] is False


# ------------------------------------------------------------------------ robustness
class TestRobustness:
    @pytest.mark.parametrize("chunk", ["a" * 1000, "1" * 1000, "a." * 500, "a @ " * 250,
                                       "house " * 200, "+1 " * 300])
    def test_large_adversarial_input_is_fast(self, chunk):
        text = chunk * 100   # about 100k characters
        start = time.perf_counter()
        detect_doxxing(text)
        assert time.perf_counter() - start < 2.0
