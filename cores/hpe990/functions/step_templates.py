"""UI-ID-bound draft step generation, independent of executing Emulator actions."""

import json
from html import escape
from string import Formatter

from gherkin.parser import Parser

from cores.hpe990.common.paths import hpe990_folders


def _pending_label(field):
    labels = {
        "ui_type": "입력유형",
        "ui_name": "요소 이름",
        "path": "진입 경로",
        "value": "시험값",
        "options": "선택 목록",
        "open_action": "호출 방법",
        "close_action": "닫기 방법",
        "expected_input_result": "입력 처리 결과",
        "expected_action_result": "버튼 동작 결과",
        "expected_display_value": "표시 기대값",
        "minimum": "최소값",
        "maximum": "최대값",
        "below_minimum": "최소값 미만 시험값",
        "above_maximum": "최대값 초과 시험값",
        "at_or_above_minimum": "최소값 이상 시험값",
        "at_or_below_maximum": "최대값 이하 시험값",
        "change_action": "설정 변경 방법",
        "save_action": "저장 방법",
        "cancel_action": "취소 방법",
        "reopen_action": "재진입 방법",
        "restore_action": "복구 방법",
        "expected_save_result": "저장 기대 결과",
        "expected_cancel_result": "취소 기대 결과",
        "first_value": "첫 번째 선택값",
        "second_value": "두 번째 선택값",
        "value_description": "선택값 설명",
        "screen_expected_result": "진입 화면 기대 결과",
        "tab_select_action": "재진입 탭 선택 방법",
        "scroll_to_element": "요소까지 스크롤 방법",
        "close_expected_result": "창 닫기 기대 결과",
        "setting_name": "검증할 설정 요소",
        "empty_value": "빈 값 시험 입력",
        "non_numeric_value": "비숫자 시험 입력",
    }
    if field.endswith("_result") and field[:-7] in labels:
        return labels[field[:-7]] + " 처리 결과 미확정"
    return labels.get(field, field) + " 미확정"


def _authored_hints():
    source = hpe990_folders.D_HPE990 / "docs/bdd/preferences_general.feature"
    hints = []
    if source.exists():
        for child in Parser().parse(source.read_text(encoding="utf-8"))["feature"]["children"]:
            scenario = child.get("scenario", {})
            kinds = [
                t["name"][6:] for t in scenario.get("tags", []) if t["name"].startswith("@type-")
            ]
            if kinds:
                hints.append((scenario["name"].split(" ", 1)[-1], kinds[0]))
    return hints


def _type_hint(element, authored):
    name = element.get("name") or ""
    if name.startswith("UI_GENERAL::"):
        _, kind, label = name.split("::", 2)
        direct = {"COMBO": "option-selector", "INPUT": "input-field", "STATIC_DATA": "display"}
        if kind == "STATIC_DATA":
            return "display", "observed_static_data_name"
        for title, candidate in authored:
            if title.startswith(label + " ") and candidate in (
                "option-selector",
                "number",
                "radio",
                "checkbox",
                "input-field",
                "button",
            ):
                return candidate, "authored_draft_type_unverified"
        if kind in direct:
            return direct[kind], "native_name_hint_unverified"
    provider = {
        "Button": "button",
        "ComboBox": "option-selector",
        "Edit": "input-field",
        "CheckBox": "checkbox",
        "RadioButton": "radio",
        "Text": "display",
        "Window": "window",
        "Menu": "popup",
    }
    if element.get("control_type") in provider:
        return provider[element["control_type"]], "provider_type_hint_unverified"
    if name.startswith(("pushButton", "widget_click")):
        return "button", "native_name_hint_unverified"
    if "parent" in element and not element["parent"]:
        return "window", "native_root_hint_unverified"
    return "unknown", "unresolved_type"


def generate_drafts(elements, templates, bindings, authored=None):
    """One binding per UI ID; unresolved fields stay concrete pending placeholders."""
    formatter = Formatter()
    drafts = []
    for element in elements:
        ui_id = element["ui_id"]
        binding = bindings.get(ui_id, {})
        candidate, basis = _type_hint(element, authored or [])
        kind = binding.get("ui_type", candidate)
        if kind not in templates:
            raise ValueError(f"Unknown template type {kind!r} for {ui_id}")
        verified = binding.get("type_verified") is True and kind != "unknown"
        name = element.get("name") or f"이름 미확정 요소 {ui_id}"
        parameters = {"name": name.split("::")[-1]}
        if name.startswith("UI_GENERAL::"):
            parameters["path"] = "Setup > Preferences > General 탭 선택"
        supplied = binding.get("parameters", {})
        if not isinstance(supplied, dict) or any(
            not isinstance(v, str) or not v.strip() for v in supplied.values()
        ):
            raise ValueError(f"Template parameters must be nonempty strings: {ui_id}")
        if "name" in supplied:
            raise ValueError("UI name comes from the identity SSOT, not a template override")
        parameters.update(supplied)
        selected = [kind] + binding.get("variants", [])
        if kind == "number" and "number-boundary" not in selected:
            selected.append("number-boundary")
        if kind == "number":
            selected += [
                variant
                for variant in ("number-invalid", "number-boundary-extended")
                if variant in templates and variant not in selected
            ]
        cases = []
        for template_id in dict.fromkeys(selected):
            if template_id not in templates:
                raise ValueError(f"Unknown variant {template_id!r}")
            definition = templates[template_id]
            pending = set()

            def resolve(text):
                for _, field, _, _ in formatter.parse(text):
                    if field and field not in parameters:
                        pending.add(field)
                return formatter.vformat(
                    text,
                    (),
                    {
                        field: parameters.get(field, f"[{_pending_label(field)}]")
                        for _, field, _, _ in formatter.parse(text)
                        if field
                    },
                )

            title = resolve(definition["title"])
            steps = [
                {
                    "Step": index,
                    "Steps": [resolve(t) for t in group["Steps"]],
                    "Expected Result": [resolve(t) for t in group["Expected Result"]],
                }
                for index, group in enumerate(definition["steps"], 1)
            ]
            if not verified:
                pending.add("ui_type")
            if not element.get("name"):
                pending.add("ui_name")
            cases.append(
                {
                    "template_id": template_id,
                    "source_tc_ids": definition.get("source_tc_ids", []),
                    "source_limit": definition.get("source_limit"),
                    "title": title,
                    "preconditions": [
                        {"Step": index, "Steps": [resolve(text) for text in row["Steps"]]}
                        for index, row in enumerate(definition.get("preconditions", []), 1)
                    ]
                    or [
                        {
                            "Step": 1,
                            "Steps": [
                                "시험 환경 및 복구 준비",
                                "해당 UI 진입 조건과 시험 전 값·복구 방법 확인",
                            ],
                        }
                    ],
                    "steps": steps,
                    "pending_specifications": sorted(pending),
                    "pending_labels": [_pending_label(field) for field in sorted(pending)],
                    "status": "draft",
                    "executable": False,
                }
            )
        drafts.append(
            {
                "ui_id": ui_id,
                "name": name,
                "ui_type": kind,
                "type_verified": verified,
                "type_basis": "explicit_binding" if binding else basis,
                "identity_scope": element.get("identity_scope"),
                "cases": cases,
            }
        )
    return drafts


def _review_html(drafts):
    parts = [
        '<!doctype html><html lang="ko"><meta charset="utf-8"><title>UI Step 템플릿 검수</title>',
        "<style>body{font-family:Segoe UI,Malgun Gothic;margin:32px;color:#20334a}"
        "table{border-collapse:collapse;width:100%;margin:16px 0}td,th{border:1px solid #ccd9e6;"
        "padding:12px;vertical-align:top;text-align:left}th{background:#eaf1f8}"
        "small{color:#a12626}article{margin-bottom:32px}</style><h1>UI Step 템플릿 검수</h1>"
        "<p>수집 요소별 TC 초안 · 미확정 명세 표시 · 시험 실행 결과 없음</p>",
    ]
    for draft in drafts:
        for case in draft["cases"]:
            parts += [
                f"<article><h2>{escape(draft['ui_id'])} · {escape(case['title'])}</h2>",
                "<small>미확정: "
                + escape(", ".join(case["pending_labels"]) or "없음")
                + "</small>",
                "<h3>Pre-condition</h3><table><tr><th>Step</th><th>Steps</th></tr>",
            ]
            if case.get("source_limit"):
                parts.append("<p>" + escape(case["source_limit"]) + "</p>")
            for row in case["preconditions"]:
                parts.append(
                    f"<tr><td>{row['Step']}</td><td>"
                    + "<br>".join(map(escape, row["Steps"]))
                    + "</td></tr>"
                )
            parts.append(
                "</table><table><tr><th>Step</th><th>Steps</th><th>Expected Result</th></tr>"
            )
            for row in case["steps"]:
                parts.append(
                    f"<tr><td>{row['Step']}</td><td>"
                    + "<br>".join(map(escape, row["Steps"]))
                    + "</td><td>"
                    + "<br>".join(map(escape, row["Expected Result"]))
                    + "</td></tr>"
                )
            parts.append("</table></article>")
    return "".join(parts) + "</html>"


def template_catalog(session_id, ui_ids=None):
    from cores.hpe990.functions.ui import ui_catalog

    catalog = ui_catalog(session_id)
    templates = json.loads(hpe990_folders.F_HPE990_STEP_TEMPLATES.read_text(encoding="utf-8"))[
        "templates"
    ]
    bindings = json.loads(hpe990_folders.F_HPE990_STEP_BINDINGS.read_text(encoding="utf-8"))[
        "bindings"
    ]
    elements = {}
    sources = {}
    for item in catalog["supplemental_elements"] + catalog["controls"]:
        element = item["identity"]
        elements[element["ui_id"]] = element
        sources.setdefault(element["ui_id"], set()).update(item["observations"])
    if ui_ids is not None:
        if set(ui_ids) - elements.keys():
            raise ValueError("Requested UI IDs are not in the session catalog")
        elements = {key: value for key, value in elements.items() if key in ui_ids}
    drafts = generate_drafts(list(elements.values()), templates, bindings, _authored_hints())
    for draft in drafts:
        draft["evidence"] = sorted(sources[draft["ui_id"]])
        observed = elements[draft["ui_id"]]
        draft["parent_ui_id"] = observed.get("parent_ui_id")
        draft["root_ui_id"] = observed.get("root_ui_id")
    destination = hpe990_folders.D_HPE990_EVIDENCE / "ui" / session_id / "step-templates"
    destination.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "session_id": session_id,
        "template_source": str(hpe990_folders.F_HPE990_STEP_TEMPLATES),
        "bindings_source": str(hpe990_folders.F_HPE990_STEP_BINDINGS),
        "templates": templates,
        "drafts": drafts,
        "element_count": len(drafts),
        "case_count": sum(len(d["cases"]) for d in drafts),
        "unverified_type_count": sum(not d["type_verified"] for d in drafts),
        "whole_application_complete": False,
        "bdd_executed": False,
        "json": str(destination / "catalog.json"),
        "html": str(destination / "review.html"),
    }
    (destination / "catalog.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (destination / "review.html").write_text(_review_html(drafts), encoding="utf-8")
    return report
