"""Extract parameterized type templates from the current authored TC scenarios."""

import hashlib
import json
from html import escape

from gherkin.parser import Parser

from cores.hpe990.common.paths import hpe990_folders


def compile_tc_templates(source: str, existing: dict) -> dict:
    scenarios = {}
    for child in Parser().parse(source)["feature"]["children"]:
        scenario = child.get("scenario", {})
        for tag in scenario.get("tags", []):
            if tag["name"].startswith("@TC-"):
                scenarios[tag["name"][1:]] = scenario
    representatives = {
        "option-selector": ("TC-002", "Language"),
        "radio": ("TC-003", "Beep Sound"),
        "checkbox": ("TC-013", "Sleep Mode"),
        "number": ("TC-014", "Wait (minutes)"),
        "number-boundary": ("TC-015", "Wait (minutes)"),
        "number-invalid": ("TC-016", "Wait (minutes)"),
        "input-field": ("TC-030", "Config DB History"),
        "button-save": ("TC-020", "Save"),
        "button-cancel": ("TC-021", "Cancel"),
    }
    document = json.loads(json.dumps(existing))
    for kind, (tc_id, name) in representatives.items():
        scenario = scenarios[tc_id]
        replacements = {
            "Setup > Preferences > General 탭 선택": "{path}",
            "Preferences 창의 General 탭과 설정 영역이 표시된다": "{screen_expected_result}",
            "Preferences 창이 열려 있으면 닫기 후 재진입": "{reopen_action}",
            "Preferences를 다시 진입": "{reopen_action}",
            "General 탭 선택": "{tab_select_action}",
            "General 설정 영역에서 Config DB History 항목까지 스크롤": "{scroll_to_element}",
            "Preferences 창이 닫힌다": "{close_expected_result}",
            "Save 클릭": "{save_action}",
            "Cancel 클릭": "{cancel_action}",
            "승인된 다른 지원 언어": "{second_value}",
            "선택한 지원 언어": "{second_value}",
            "저장한 지원 언어": "{second_value}",
            "원래 언어": "원래 선택값",
            "시험 전 언어": "시험 전 선택값",
            "지원 언어": "{value_description}",
            "English": "{first_value}",
            "OFF": "{first_value}",
            "ON": "{second_value}",
            "승인된 시험값": "{value}",
            "승인된 최소값": "{minimum}",
            "승인된 최대값": "{maximum}",
            "허용 범위 미만 값": "{below_minimum}",
            "허용 범위 초과 값": "{above_maximum}",
            "비숫자 문자": "{non_numeric_value}",
            "빈 값": "{empty_value}",
            "확정된 처리 규칙과 일치하는 결과": "{invalid_expected_result}",
            "시험 전 값과 다른 선택지": "{value}",
            "변경한 선택지": "{value}",
        }
        if kind.startswith("button-"):
            replacements["Beep Sound"] = "{setting_name}"
        replacements[name] = "{name}"

        def parameterize(text, expected=False):
            for literal, variable in sorted(replacements.items(), key=lambda item: -len(item[0])):
                text = text.replace(literal, variable)
            if expected:
                text = text.replace("표시된다.", "보여야 합니다.").replace(
                    "표시된다", "보여야 합니다."
                )
            return text

        groups, prerequisites, phase = [], [], "precondition"
        for step in scenario["steps"]:
            keyword = step["keyword"].strip()
            if keyword == "When":
                groups.append({"Steps": [], "Expected Result": []})
                phase = "action"
            elif keyword == "Then":
                phase = "expected"
            if phase == "precondition":
                prerequisites.append(
                    {
                        "Steps": [parameterize(step["text"])]
                        + [
                            parameterize(line)
                            for line in step.get("docString", {}).get("content", "").splitlines()
                        ]
                    }
                )
            else:
                text = parameterize(step["text"], phase == "expected")
                if kind == "number-invalid" and phase == "expected" and 2 <= len(groups) <= 5:
                    field = [
                        "empty_value_result",
                        "non_numeric_value_result",
                        "below_minimum_result",
                        "above_maximum_result",
                    ][len(groups) - 2]
                    text = text.replace("{invalid_expected_result}", "{" + field + "}")
                groups[-1]["Steps" if phase == "action" else "Expected Result"].append(text)
        document["templates"][kind] = {
            "title": parameterize(scenario["name"].removeprefix(tc_id + " ")),
            "preconditions": prerequisites,
            "steps": groups,
            "source_tc_ids": [tc_id],
            "type_verified": False,
            "source_status": "authored_draft",
        }
        related = []
        for candidate_id, candidate in scenarios.items():
            tags = {tag["name"] for tag in candidate.get("tags", [])}
            same_type = "@type-" + kind in tags
            if kind.startswith("number"):
                same_type = "@type-number" in tags and (
                    (kind == "number-boundary" and "경계값" in candidate["name"])
                    or (kind == "number-invalid" and "잘못된" in candidate["name"])
                    or (kind == "number" and "저장값 확인" in candidate["name"])
                )
            if same_type:
                related.append(candidate_id)
        document["templates"][kind]["related_tc_ids"] = related
        if kind == "input-field":
            document["templates"][kind]["source_limit"] = (
                "TC-030의 편집 가능 가정은 미검증. STATIC_DATA에는 적용하지 않고 표시 템플릿 사용."
            )
    # Keep additional inclusive/exclusive boundary patterns alongside TC-015's full flow.
    document["templates"]["number-boundary-extended"] = (
        document["templates"]["number-boundary-extended"]
        if "number-boundary-extended" in document["templates"]
        else existing["templates"]["number-boundary"]
    )
    for definition in document["templates"].values():
        for group in definition["steps"]:
            group["Expected Result"] = [
                text.replace("표시된다.", "보여야 합니다.").replace("표시된다", "보여야 합니다.")
                for text in group["Expected Result"]
            ]
    document["schema_version"] = 2
    document["derived_from"] = "cores/hpe990/docs/bdd/preferences_general.feature"
    document["source_sha256"] = hashlib.sha256(source.encode()).hexdigest()
    document["authored_template_count"] = len(representatives)
    return document


def refresh_templates_from_tcs():
    source = hpe990_folders.D_HPE990 / "docs/bdd/preferences_general.feature"
    target = hpe990_folders.F_HPE990_STEP_TEMPLATES
    document = compile_tc_templates(
        source.read_text(encoding="utf-8"), json.loads(target.read_text(encoding="utf-8"))
    )
    target.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output = hpe990_folders.D_HPE990 / "docs/bdd/ui_step_templates.md"
    lines = [
        "# 입력유형별 TC Step 템플릿",
        "",
        "현재 TC에서 추출한 작성 초안. 실제 실행 결과 없음.",
        "",
    ]
    for kind, definition in document["templates"].items():
        if not definition.get("source_tc_ids"):
            continue
        lines += [
            f"## {kind}",
            "",
            "근거: " + ", ".join(definition["source_tc_ids"]),
            "",
            definition["title"],
            "",
            "| Step | Steps |",
            "|---|---|",
        ]
        for index, prerequisite in enumerate(definition["preconditions"], 1):
            lines.append(
                f"| {index} | "
                + "<br>".join(escape(t).replace("|", "\\|") for t in prerequisite["Steps"])
                + " |"
            )
        lines += ["", "| Step | Steps | Expected Result |", "|---|---|---|"]
        for index, group in enumerate(definition["steps"], 1):
            cells = [
                "<br>".join(escape(t).replace("|", "\\|") for t in group[key])
                for key in ("Steps", "Expected Result")
            ]
            lines.append(f"| {index} | {cells[0]} | {cells[1]} |")
        if definition.get("source_limit"):
            lines += ["", definition["source_limit"]]
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")
    return {
        "source": str(source),
        "template_source": str(target),
        "markdown": str(output),
        "authored_template_count": document["authored_template_count"],
        "bdd_executed": False,
    }
