"""Apply canonical TC up dictionary wording to generated expectations."""

from cores.hpe990.rules.scenarios.tc_up_dictionary import EXPECTED_RESULT_REPLACEMENTS


def normalize_expected_result(text: str) -> str:
    for old, new in EXPECTED_RESULT_REPLACEMENTS:
        text = text.replace(old, new)
    return text
