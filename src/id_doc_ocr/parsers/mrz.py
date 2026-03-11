from __future__ import annotations

from dataclasses import dataclass


MRZ_WEIGHTS = [7, 3, 1]


def _char_value(ch: str) -> int:
    if ch == "<":
        return 0
    if ch.isdigit():
        return int(ch)
    if "A" <= ch <= "Z":
        return ord(ch) - ord("A") + 10
    raise ValueError(f"Unsupported MRZ character: {ch}")


def compute_check_digit(data: str) -> str:
    total = 0
    for i, ch in enumerate(data):
        total += _char_value(ch) * MRZ_WEIGHTS[i % 3]
    return str(total % 10)


@dataclass
class TD3MRZ:
    document_code: str
    issuing_country: str
    surname: str
    given_names: str
    passport_number: str
    passport_number_check: str
    nationality: str
    birth_date: str
    birth_date_check: str
    sex: str
    expiry_date: str
    expiry_date_check: str
    personal_number: str
    personal_number_check: str
    final_check: str

    @property
    def composite_data(self) -> str:
        return (
            self.passport_number
            + self.passport_number_check
            + self.birth_date
            + self.birth_date_check
            + self.expiry_date
            + self.expiry_date_check
            + self.personal_number
            + self.personal_number_check
        )


def _split_names(raw: str) -> tuple[str, str]:
    parts = raw.split("<<", 1)
    surname = parts[0].replace("<", " ").strip()
    given = parts[1].replace("<", " ").strip() if len(parts) > 1 else ""
    return surname, given


def parse_td3(lines: list[str]) -> TD3MRZ:
    if len(lines) != 2:
        raise ValueError("TD3 MRZ requires exactly 2 lines")
    line1, line2 = [line.strip().upper() for line in lines]
    if len(line1) != 44 or len(line2) != 44:
        raise ValueError("TD3 MRZ lines must each be 44 characters")

    document_code = line1[0:2]
    issuing_country = line1[2:5]
    surname, given_names = _split_names(line1[5:44])

    passport_number = line2[0:9]
    passport_number_check = line2[9]
    nationality = line2[10:13]
    birth_date = line2[13:19]
    birth_date_check = line2[19]
    sex = line2[20]
    expiry_date = line2[21:27]
    expiry_date_check = line2[27]
    personal_number = line2[28:42]
    personal_number_check = line2[42]
    final_check = line2[43]

    return TD3MRZ(
        document_code=document_code,
        issuing_country=issuing_country,
        surname=surname,
        given_names=given_names,
        passport_number=passport_number,
        passport_number_check=passport_number_check,
        nationality=nationality,
        birth_date=birth_date,
        birth_date_check=birth_date_check,
        sex=sex,
        expiry_date=expiry_date,
        expiry_date_check=expiry_date_check,
        personal_number=personal_number,
        personal_number_check=personal_number_check,
        final_check=final_check,
    )


def validate_td3(mrz: TD3MRZ) -> list[str]:
    issues: list[str] = []
    if compute_check_digit(mrz.passport_number) != mrz.passport_number_check:
        issues.append("passport_number_check_failed")
    if compute_check_digit(mrz.birth_date) != mrz.birth_date_check:
        issues.append("birth_date_check_failed")
    if compute_check_digit(mrz.expiry_date) != mrz.expiry_date_check:
        issues.append("expiry_date_check_failed")
    if compute_check_digit(mrz.personal_number) != mrz.personal_number_check:
        issues.append("personal_number_check_failed")
    if compute_check_digit(mrz.composite_data) != mrz.final_check:
        issues.append("final_check_failed")
    return issues
