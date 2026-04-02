from __future__ import annotations

import re
from typing import Any


DATE_RE = re.compile(r"(20\d{2}|19\d{2})[年\-/.](\d{1,2})[月\-/.](\d{1,2})日?")
NAME_RE = r"[\u4e00-\u9fa5·]{2,8}"
ID_RE = re.compile(r"\b(\d{17}[\dXx]|\d{15})\b")
TITLE_HINTS = (
    "抚养关系证明",
    "监护关系证明",
    "关系证明",
    "情况证明",
    "证明",
)
LABEL_ALIASES = {
    "child_name": ["子女姓名", "儿童姓名", "未成年人姓名", "被抚养人", "孩子姓名", "姓名"],
    "guardian_name": ["抚养人", "监护人", "法定监护人", "申请人", "家长姓名"],
    "relation": ["关系", "与子女关系", "与被抚养人关系", "亲属关系"],
    "child_birth_date": ["出生日期", "出生年月日", "子女出生日期", "儿童出生日期"],
    "child_id_number": ["子女身份证号", "儿童身份证号", "未成年人身份证号", "被抚养人身份证号"],
    "guardian_id_number": ["抚养人身份证号", "监护人身份证号", "申请人身份证号", "法定监护人身份证号"],
    "subject_address": ["现居住地址", "居住地址", "住址", "户籍地址", "常住地址"],
    "purpose": ["用途", "证明用途", "使用用途", "事由"],
    "issuing_authority": ["出具单位", "证明单位", "出具机关", "盖章单位", "签发机关"],
    "issue_date": ["出具日期", "证明日期", "签发日期", "日期"],
}
RELATION_KEYWORDS = (
    "父子关系",
    "父女关系",
    "母子关系",
    "母女关系",
    "祖孙关系",
    "外祖孙关系",
    "监护关系",
    "抚养关系",
    "之父",
    "之母",
    "祖父",
    "祖母",
    "外祖父",
    "外祖母",
)
AUTHORITY_FEATURE_PATTERNS = {
    "residents_committee": re.compile(r"居民委员会|居委会"),
    "village_committee": re.compile(r"村民委员会|村委会"),
    "subdistrict_office": re.compile(r"街道办事处|街道办"),
    "police_station": re.compile(r"公安派出所|派出所"),
    "town_government": re.compile(r"镇人民政府|乡人民政府"),
    "civil_affairs": re.compile(r"民政局|婚姻登记|救助管理"),
    "community_service_center": re.compile(r"社区事务受理服务中心|便民服务中心"),
}
FREE_TEXT_PATTERNS = [
    re.compile(
        rf"(?:兹证明(?:：|:)?\s*)?(?P<guardian>{NAME_RE})[^。\n]{{0,40}}系(?:未成年人)?(?P<child>{NAME_RE})之(?P<relation>父|母|祖父|祖母|外祖父|外祖母)"
    ),
    re.compile(
        rf"(?P<guardian>{NAME_RE})(?:，|,|\s)*(?:系|与)(?:未成年人)?(?P<child>{NAME_RE})(?:之)?(?P<relation>父亲|母亲|父亲监护人|母亲监护人|监护人|法定监护人|父子关系|父女关系|母子关系|母女关系|祖孙关系|外祖孙关系|抚养关系|监护关系|之父|之母|祖父|祖母|外祖父|外祖母)"
    ),
    re.compile(
        rf"(?P<child>{NAME_RE})(?:，|,|\s)*由(?P<guardian>{NAME_RE})(?:长期|一直|依法)?(?P<relation>抚养|监护|照料)"
    ),
    re.compile(
        rf"兹证明(?:：|:)?(?P<guardian>{NAME_RE}).{{0,18}}(?P<child>{NAME_RE}).{{0,12}}存在(?P<relation>抚养关系|监护关系)"
    ),
]
CHILD_BIRTH_INLINE_RE = re.compile(rf"(?P<child>{NAME_RE})[，,]\s*(?P<date>(20\d{{2}}|19\d{{2}})[年\-/.]\d{{1,2}}[月\-/.]\d{{1,2}}日?)出生")
CHILD_ID_INLINE_RE = re.compile(rf"(?P<child>{NAME_RE})[^。\n]{{0,20}}身份证号\s*(?P<id>\d{{17}}[\dXx]|\d{{15}})")
GUARDIAN_ID_INLINE_RE = re.compile(rf"(?P<guardian>{NAME_RE})[^。\n]{{0,20}}身份证号\s*(?P<id>\d{{17}}[\dXx]|\d{{15}})")
PURPOSE_RE = re.compile(r"(?:本证明)?用于[\u4e00-\u9fa5A-Za-z0-9、，,。；;（）()]{2,40}")


def _rows(ocr_result: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for item in ocr_result.get("lines", []):
        text = str(item.get("text") or "").strip()
        if text:
            rows.append(text)
    if not rows and ocr_result.get("text"):
        rows.extend(line.strip() for line in str(ocr_result["text"]).splitlines() if line.strip())
    return rows


def _normalize_text(text: str) -> str:
    return (
        text.replace("：", ":")
        .replace("（", "(")
        .replace("）", ")")
        .replace("，", ",")
        .replace(" ", " ")
        .strip()
    )


def _after_label(text: str, aliases: list[str]) -> str | None:
    normalized = _normalize_text(text)
    upper = normalized.upper()
    for alias in aliases:
        alias_upper = alias.upper()
        if upper.startswith(alias_upper + ":"):
            return normalized[len(alias) + 1 :].strip()
        if upper == alias_upper:
            return ""
    return None


def _collect_labeled_value(rows: list[str], field: str) -> str | None:
    aliases = LABEL_ALIASES[field]
    for idx, row in enumerate(rows):
        value = _after_label(row, aliases)
        if value is None:
            continue
        if value:
            return value
        if idx + 1 < len(rows):
            candidate = rows[idx + 1].strip()
            if candidate:
                return candidate
    return None


def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    match = DATE_RE.search(value)
    if not match:
        return None
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _extract_id_number(value: str | None) -> str | None:
    if not value:
        return None
    compact = re.sub(r"\s+", "", value).upper()
    match = ID_RE.search(compact)
    return match.group(1) if match else None


def _infer_title(rows: list[str]) -> str | None:
    for row in rows[:5]:
        if "证明" in row and any(hint in row for hint in TITLE_HINTS):
            return row.strip()
    return None


def _normalize_relation(value: str | None, relation_statement: str | None = None) -> str | None:
    text = " ".join(part for part in [value or "", relation_statement or ""] if part)
    if not text:
        return None
    if "监护" in text:
        return "监护关系"
    if "抚养" in text:
        return "抚养关系"
    if "父子" in text:
        return "父子关系"
    if "父女" in text:
        return "父女关系"
    if "母子" in text:
        return "母子关系"
    if "母女" in text:
        return "母女关系"
    if "之父" in text or "父亲" in text:
        return "父/子女关系"
    if "之母" in text or "母亲" in text:
        return "母/子女关系"
    if "祖孙" in text and "外祖" not in text:
        return "祖孙关系"
    if "外祖孙" in text:
        return "外祖孙关系"
    compact = value.strip() if value else None
    return compact


def _infer_relation_statement(rows: list[str]) -> str | None:
    sentences: list[str] = []
    for row in rows:
        if row.endswith("证明") and len(row) <= 12:
            continue
        sentences.extend(part.strip() for part in re.split(r"[。；;]", row) if part.strip())

    for sentence in sentences:
        if any(keyword in sentence for keyword in RELATION_KEYWORDS) or ("抚养" in sentence and "证明" not in sentence):
            return sentence
    joined = "\n".join(rows)
    for pattern in FREE_TEXT_PATTERNS:
        match = pattern.search(joined)
        if match:
            return match.group(0).strip()
    return None


def _infer_names_from_statement(statement: str | None) -> tuple[str | None, str | None, str | None]:
    if not statement:
        return None, None, None
    for pattern in FREE_TEXT_PATTERNS:
        match = pattern.search(statement)
        if not match:
            continue
        guardian = match.groupdict().get("guardian")
        child = match.groupdict().get("child")
        relation = match.groupdict().get("relation")
        if relation in {"抚养", "监护", "照料"}:
            relation = f"{relation}关系"
        elif relation == "父":
            relation = "父/子女关系"
        elif relation == "母":
            relation = "母/子女关系"
        elif relation in {"祖父", "祖母"}:
            relation = "祖孙关系"
        elif relation in {"外祖父", "外祖母"}:
            relation = "外祖孙关系"
        return child, guardian, relation
    return None, None, None


def _infer_inline_birth_date(rows: list[str], child_name: str | None) -> str | None:
    joined = "\n".join(rows)
    if child_name:
        pattern = re.compile(rf"{re.escape(child_name)}[，,]\s*((20\d{{2}}|19\d{{2}})[年\-/.]\d{{1,2}}[月\-/.]\d{{1,2}}日?)出生")
        match = pattern.search(joined)
        if match:
            return _normalize_date(match.group(1))
    match = CHILD_BIRTH_INLINE_RE.search(joined)
    return _normalize_date(match.group("date")) if match else None



def _infer_inline_id(rows: list[str], name: str | None, kind: str) -> str | None:
    joined = "\n".join(rows)
    if name:
        pattern = re.compile(rf"{re.escape(name)}.{{0,20}}身份证号\s*(\d{{17}}[\dXx]|\d{{15}})")
        match = pattern.search(joined)
        if match:
            return match.group(1).upper()
    pattern = CHILD_ID_INLINE_RE if kind == "child" else GUARDIAN_ID_INLINE_RE
    match = pattern.search(joined)
    return match.group("id").upper() if match else None



def _infer_issue_date(rows: list[str]) -> str | None:
    labeled = _normalize_date(_collect_labeled_value(rows, "issue_date"))
    if labeled:
        return labeled
    for row in reversed(rows[-4:]):
        normalized = _normalize_date(row)
        if normalized:
            return normalized
    return None


def _infer_purpose(rows: list[str]) -> str | None:
    labeled = _collect_labeled_value(rows, "purpose")
    if labeled:
        return labeled
    joined = "\n".join(rows)
    match = PURPOSE_RE.search(joined)
    return match.group(0) if match else None


def _extract_authority_features(rows: list[str]) -> list[str]:
    joined = "\n".join(rows)
    features = [name for name, pattern in AUTHORITY_FEATURE_PATTERNS.items() if pattern.search(joined)]
    return sorted(features)


def parse_custody_relationship_certificate_fields(ocr_result: dict[str, Any]) -> dict[str, Any]:
    rows = _rows(ocr_result)

    relation_statement = _infer_relation_statement(rows)
    inferred_child_name, inferred_guardian_name, inferred_relation = _infer_names_from_statement(relation_statement)

    child_name = _collect_labeled_value(rows, "child_name") or inferred_child_name
    guardian_name = _collect_labeled_value(rows, "guardian_name") or inferred_guardian_name
    relation = _normalize_relation(_collect_labeled_value(rows, "relation"), relation_statement) or inferred_relation
    if relation in {None, "父/子女关系", "母/子女关系", "祖孙关系", "外祖孙关系"} and any("抚养" in row for row in rows):
        relation = "抚养关系"
    if relation is None and any("监护" in row for row in rows):
        relation = "监护关系"
    issuing_authority = _collect_labeled_value(rows, "issuing_authority")

    if not issuing_authority:
        for row in reversed(rows[-4:]):
            if any(pattern.search(row) for pattern in AUTHORITY_FEATURE_PATTERNS.values()):
                issuing_authority = row.strip(" ：:")
                break

    child_birth_date = _normalize_date(_collect_labeled_value(rows, "child_birth_date")) or _infer_inline_birth_date(rows, child_name)
    child_id_number = _extract_id_number(_collect_labeled_value(rows, "child_id_number")) or _infer_inline_id(rows, child_name, "child")
    guardian_id_number = _extract_id_number(_collect_labeled_value(rows, "guardian_id_number")) or _infer_inline_id(rows, guardian_name, "guardian")

    return {
        "doc_type": "custody_relationship_certificate",
        "certificate_title": _infer_title(rows),
        "child_name": child_name,
        "guardian_name": guardian_name,
        "relation": relation,
        "relation_statement": relation_statement,
        "child_birth_date": child_birth_date,
        "child_id_number": child_id_number,
        "guardian_id_number": guardian_id_number,
        "subject_address": _collect_labeled_value(rows, "subject_address"),
        "purpose": _infer_purpose(rows),
        "issuing_authority": issuing_authority,
        "issue_date": _infer_issue_date(rows),
        "authority_features": _extract_authority_features(rows),
    }
