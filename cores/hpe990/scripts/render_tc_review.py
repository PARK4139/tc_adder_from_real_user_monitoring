"""Export authored Gherkin drafts as numbered TC tables for human review."""

import json
import re
from html import escape
from pathlib import Path
from urllib.parse import unquote

from gherkin.parser import Parser

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.tc_wording import normalize_expected_result

TEST_TARGET = {
    "model": "HPE990",
    "version": "1.22",
    "executable": "HPE990_v1.22_251010.exe",
}


def chip_class(label):
    if label == "검수 완료":
        return "reviewed"
    if label == "검수 대기":
        return "awaiting"
    return "actual" if label == ACTUAL_BEHAVIOR_LABEL else "pending"


STYLE = """
:root{color-scheme:light;font-family:'Segoe UI','Malgun Gothic',sans-serif;color:#20334a;background:#f3f6fa}
*{box-sizing:border-box}[hidden]{display:none!important}body{margin:0}header{background:#eaf1f8;color:#20334a;padding:28px 32px}header>p{margin:0;color:#526a82;font-size:14px}
.toolbar{display:flex;gap:12px;align-items:center;padding:18px 30px;flex-wrap:wrap;position:sticky;top:0;background:#f3f6fa;z-index:2}
input{font:inherit;padding:10px 14px;border:1px solid #c5d3e2;border-radius:7px;background:white;min-width:240px;flex:1}#count{font-size:13px;color:#536f8b}
.layout{display:grid;grid-template-columns:var(--tree-width,350px) 10px minmax(0,1fr);gap:8px;padding:0 30px 32px}
.tree-resizer{position:sticky;top:82px;align-self:start;height:82vh;cursor:col-resize;touch-action:none;border-radius:5px;display:flex;justify-content:center}.tree-resizer:before{content:"";width:3px;background:#ccd9e6;border-radius:3px}.tree-resizer:hover:before,.tree-resizer:focus-visible:before{background:#3074bd}.tree-resizer:focus-visible{outline:2px solid #3074bd;outline-offset:2px}body.resizing-tree{cursor:col-resize;user-select:none}
.tree-heading{display:flex;align-items:center;justify-content:space-between;gap:6px;margin:0 0 12px;padding:4px 0 10px;border-bottom:1px solid #dae4ee}.tree-heading .review-heading{font-size:16px;white-space:nowrap;margin:0;padding:0;border:0}.tree-actions{display:flex;gap:4px;flex:0 0 auto;justify-content:flex-end}.tree-actions button{font:inherit;font-size:10px;white-space:nowrap;padding:6px;border:1px solid #c5d3e2;border-radius:6px;background:white;color:#315b82;cursor:pointer;box-shadow:0 2px 8px #20334a22}.tree-actions button:hover{background:#f0f5fa}.masthead{border-bottom-color:#cbd9e7}.masthead .tree-actions button{background:#315b82;color:#f5f9ff;border-color:#315b82;box-shadow:none}.masthead .tree-actions button:hover{background:#274b6d}
.tree-panel{position:sticky;top:82px;align-self:start;min-width:0}nav{max-height:calc(82vh - 54px);overflow:auto;background:white;border:1px solid #dae4ee;border-radius:10px;padding:12px}
nav.tc-collapsed>a,nav.tc-collapsed .tree-children>a{display:none}
nav.tc-collapsed details[data-show-tcs="true"]>.tree-children>a{display:flex}

.review-heading{font-size:16px;margin:0 0 16px;padding:4px 0 12px;border-bottom:1px solid #dae4ee}
nav details{margin:3px 0}nav summary{display:flex;align-items:center;gap:7px;cursor:pointer;list-style:none;padding:8px 4px;color:#31516e;font-size:13px;font-weight:600;border-radius:5px}
nav summary::-webkit-details-marker{display:none}nav summary:before{content:"›";color:#8298ae;transition:transform .12s}nav details[open]>summary:before{transform:rotate(90deg)}
nav summary:hover{background:#f0f5fa}.tree-count{margin-left:auto;color:#7b8fa3;font-size:11px;font-weight:400;white-space:nowrap}.tree-children{margin-left:9px;padding-left:8px;border-left:1px solid #e1e9f2}
nav a{display:block;padding:9px 7px;text-decoration:none;color:#315b82;font-size:12px;border-left:3px solid transparent;border-bottom:1px solid #edf1f6;border-radius:5px;scroll-margin-block:16px}
nav a:hover{background:#f0f5fa}nav a[aria-current="true"]{background:#eaf3ff;border-left-color:#3074bd}.tree-leaf-top{display:flex;align-items:center;gap:6px}.tree-title{flex:1;min-width:max-content;font-size:13px;line-height:1.5;white-space:nowrap}
.tree-id{display:inline-block;flex-shrink:0;color:#8091a3;font-size:10px;line-height:1.5;white-space:nowrap}.tree-chips{display:flex;flex-direction:row;flex-wrap:nowrap;align-items:center;gap:3px;flex-shrink:0}.tree-chip{white-space:nowrap;font-size:10px;line-height:1.5;padding:2px 5px;border-radius:4px}.tree-chip.pending{background:#fff2d9;color:#8a4b08}.tree-chip.actual{background:#fde8e8;color:#a12626}mark{background:#ffdf7d;color:inherit;border-radius:2px}
article,.intro{background:white;border:1px solid #dae4ee;border-radius:10px;padding:22px;margin-bottom:22px}
article{scroll-margin-top:95px}h2{font-size:18px;margin:0 0 10px;overflow-wrap:anywhere}h3{font-size:15px}
.tc-heading{margin-bottom:10px}.tc-title{min-width:0}.tc-meta{font-size:12px;color:#66788a;line-height:1.5;margin-bottom:6px;overflow-wrap:anywhere}.tc-title-line{display:flex;align-items:center;gap:16px;min-width:0}.tc-title-line h2{flex:1;min-width:0;font-size:21px;font-weight:700;line-height:1.5;margin:0;white-space:nowrap;overflow-x:auto}.tc-id{font-size:12px;font-weight:400;color:#8091a3;margin-right:6px}.tc-chips{display:flex;flex:0 0 auto;justify-content:flex-end;flex-wrap:nowrap;gap:6px;max-width:40%;overflow-x:auto}.tc-chips .badge{flex:0 0 auto;white-space:nowrap}
.badge{display:inline-block;font-size:12px;background:#edf4fa;color:#4f6780;border-radius:5px;padding:5px 8px}
.legend-items{display:flex;flex-direction:column;gap:8px}.legend-item{display:flex;align-items:center;gap:6px;font-size:12px;color:#66788a}
.pending{background:#fff2d9;color:#8a4b08}.actual{background:#fde8e8;color:#a12626}p,li{font-size:14px;line-height:1.7}.table-wrap{overflow:auto;margin-top:16px}
table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:14px}th,td{border:1px solid #ccd9e6;padding:14px;text-align:left;vertical-align:top;line-height:1.75;overflow-wrap:anywhere}
th{background:#eaf1f8}th:first-child{width:65px;text-align:center}th:nth-child(2){width:49%}td:first-child{text-align:center;font-weight:600;background:#f7faff}
ol{margin:0;padding-left:22px}td p{margin:0}.intro{color:#46617b}.empty{padding:20px;color:#6b7e93}
.preconditions th:nth-child(2){width:auto}.precondition-details{white-space:pre-wrap;line-height:1.8;padding-left:16px}
@media(max-width:900px){header{padding:20px 14px}.layout{grid-template-columns:1fr;padding:0 14px 20px}.tree-resizer{display:none}.tree-panel{position:static}nav{max-height:200px}.toolbar{padding:14px}article{padding:14px}}
body.dark{color-scheme:dark;color:#e3edf7;background:#111923}body.dark header{background:#090f17;color:#e3edf7}body.dark header p{color:#a9bfd6}body.dark .masthead{border-bottom-color:#ffffff33}body.dark .masthead .tree-actions button{background:#202c3a;color:#e3edf7;border-color:#40536a}body.dark .masthead .tree-actions button:hover{background:#2b3b4d}body.dark .toolbar{background:#111923}body.dark input,body.dark button{background:#202c3a;color:#e3edf7;border-color:#40536a}body.dark #count{color:#a9bfd6}body.dark nav,body.dark article,body.dark .intro{background:#192431;border-color:#344457;color:#e3edf7}body.dark nav summary,body.dark nav a{color:#bdd4ec}body.dark nav summary:hover,body.dark nav a:hover{background:#25364a}body.dark nav a[aria-current="true"]{background:#253b55}body.dark .tree-children{border-color:#344457}body.dark .tc-meta,body.dark .tc-id,body.dark .tree-id,body.dark .tree-count,body.dark .legend-item{color:#a9bfd6}body.dark .tree-resizer:before{background:#40536a}body.dark th{background:#263547}body.dark th,body.dark td{border-color:#40536a}body.dark td:first-child{background:#202c3a}body.dark .badge{background:#29394b;color:#d0dfef}body.dark .pending{background:#593f1e;color:#ffd18a}body.dark .actual{background:#552b32;color:#ffb9be}body.dark .badge.reviewed,body.dark .tree-chip.reviewed{background:#1e4934;color:#9be0b4}body.dark .badge.awaiting,body.dark .tree-chip.awaiting{background:#233e5e;color:#b3d5ff}body.dark .intro{color:#bdd4ec}body.dark .empty{color:#a9bfd6}body.dark mark{background:#735b1d;color:#fff1b2}@media print{body{background:white}header{background:white;color:black;padding:0 0 16px}header p{color:#444}.toolbar,.tree-panel,.tree-resizer{display:none}.layout{display:block;padding:0}article,.intro{border:0;padding:0}.tc{display:block!important}table{font-size:11px}tr{break-inside:avoid}h2{break-after:avoid}.empty{display:none}}
"""

STYLE += """
.badge.reviewed,.tree-chip.reviewed{background:#def3e6;color:#17633b}
.badge.awaiting,.tree-chip.awaiting{background:#e4edf9;color:#24588c}
"""

SCRIPT = r"""
const themeKey='auto-emulator-dark-mode',themeButton=document.getElementById('theme-toggle');
function setTheme(dark){document.body.classList.toggle('dark',dark);themeButton.setAttribute('aria-pressed',String(dark));themeButton.textContent=dark?'\ub77c\uc774\ud2b8 \ubaa8\ub4dc':'\ub2e4\ud06c \ubaa8\ub4dc';try{localStorage.setItem(themeKey,dark?'dark':'light')}catch{}}
let savedTheme=null;try{savedTheme=localStorage.getItem(themeKey)}catch{}setTheme(savedTheme==='dark');themeButton.addEventListener('click',()=>setTheme(!document.body.classList.contains('dark')));
const layout=document.querySelector('.layout'),resizer=document.getElementById('tree-resizer');
let treeWidth=350;
try{const saved=Number(localStorage.getItem('tc-review-tree-width'));if(Number.isFinite(saved)&&saved>=240)treeWidth=saved;}catch{}
function setTreeWidth(width,persist=false){
 const maximum=Math.max(240,layout.clientWidth-60-18-360);
 treeWidth=Math.round(Math.max(240,Math.min(maximum,width)));
 layout.style.setProperty('--tree-width',treeWidth+'px');
 resizer.setAttribute('aria-valuenow',treeWidth);resizer.setAttribute('aria-valuemax',maximum);
 if(persist)try{localStorage.setItem('tc-review-tree-width',String(treeWidth));}catch{}
}
setTreeWidth(treeWidth);
window.addEventListener('resize',()=>setTreeWidth(treeWidth));
resizer.addEventListener('pointerdown',event=>{
 if(event.button!==0)return;
 event.preventDefault();resizer.setPointerCapture(event.pointerId);
 const startX=event.clientX,startWidth=treeWidth;
 document.body.classList.add('resizing-tree');
 function move(e){setTreeWidth(startWidth+e.clientX-startX);}
 function finish(){document.body.classList.remove('resizing-tree');setTreeWidth(treeWidth,true);resizer.removeEventListener('pointermove',move);resizer.removeEventListener('lostpointercapture',finish);}
 resizer.addEventListener('pointermove',move);resizer.addEventListener('lostpointercapture',finish);
});
resizer.addEventListener('keydown',event=>{
 if(!['ArrowLeft','ArrowRight','Home'].includes(event.key))return;
 event.preventDefault();setTreeWidth(event.key==='Home'?350:treeWidth+(event.key==='ArrowRight'?20:-20),true);
});

"""
SCRIPT += Path(__file__).with_name("tc_review_search.js").read_text(encoding="utf-8")


TYPE_LABELS = {
    "option-selector": "선택기",
    "radio": "라디오 버튼",
    "checkbox": "체크박스",
    "number": "숫자 입력란",
    "input-field": "입력란",
    "button": "버튼",
    "navigation": "화면·항목 확인",
    "scroll": "스크롤",
}

TYPE_DESCRIPTIONS = {
    "option-selector": "목록에서 선택",
    "radio": "하나 선택",
    "checkbox": "체크·해제",
    "number": "숫자 입력",
    "input-field": "값 입력",
    "button": "클릭 실행",
    "navigation": "화면·요소 확인",
    "scroll": "영역 이동",
}


SPECIFICATION_LABELS = {
    "@spec-language-options": "지원 언어 미확정",
    "@spec-test-value": "시험값 미확정",
    "@spec-number-range": "최소·최대값 미확정",
    "@spec-error-handling": "오류 처리 미확정",
    "@spec-input-type": "입력유형 미확정",
    "@spec-input-format": "허용 형식·범위 미확정",
    "@spec-save-display": "저장·표시 규칙 미확정",
    "@spec-option-values": "선택값 미확정",
    "@spec-click-behavior": "클릭 동작 미확정",
    "@actual-behavior-check": "실제 동작 확인 필요",
}
ACTUAL_BEHAVIOR_LABEL = "실제 동작 확인 필요"


def render_navigation(entries: list[dict]) -> str:
    """Group canonical TC identities and titles without maintaining a second catalog."""
    root = {"children": {}, "order": []}
    for entry in entries:
        node = root
        target = entry.get("test_target", TEST_TARGET)
        for label in (target["model"], target["version"], *entry["path"]):
            if label not in node["children"]:
                node["children"][label] = {"children": {}, "order": []}
                node["order"].append(("branch", label))
            node = node["children"][label]
        node["order"].append(("leaf", entry))

    def leaf(entry, label):
        identity = escape(entry["id"], quote=True)
        labels = entry.get("specifications", ["요구사항 미확정"] if entry["pending"] else [])
        chip = (
            '<span class="tree-chips">'
            + "".join(
                f'<span class="tree-chip {chip_class(label)}">{escape(label)}</span>'
                for label in labels
            )
            + "</span>"
            if labels
            else ""
        )
        return (
            f'<a href="#{identity}" title="{escape(entry["title"], quote=True)}">'
            f'<span class="tree-leaf-top">'
            + (
                f'<span class="tree-title">{escape(label)}</span>'
                if (entry.get("flat") or entry.get("kind") == "scenario") and not entry.get("force_tc_id")
                else f'<span class="tree-id">{escape(entry["id"])}</span>'
                f'<span class="tree-title">{escape(label)}</span>'
            )
            + f'{chip}</span></a>'
        )

    def branch(label, contents, key):
        count = contents.count('<a href="')
        return (
            f'<details open data-node="{escape(key, quote=True)}"><summary>'
            f'<span class="tree-label">{escape(label)}</span><span class="tree-count">{count}개</span></summary>'
            f'<div class="tree-children">{contents}</div></details>'
        )

    def render(node, key=""):
        parts = []
        for kind, item in node["order"]:
            if kind == "branch":
                child_key = key + "/" + item
                parts.append(branch(item, render(node["children"][item], child_key), child_key))
            else:
                parts.append(leaf(item, item.get("tree_title", item["title"])))
        return "".join(parts)

    return render(root)


def render_review(
    source: str,
    basic_scenarios: list[dict] | None = None,
    *,
    functions_root: bool = False,
) -> tuple[str, dict]:
    feature = Parser().parse(source)["feature"]
    cards, navigation = [], []
    identities = set()
    basic_only_ids = {
        identity
        for scenario_item in (basic_scenarios or [])
        for identity in [scenario_item.get("id", ""), *scenario_item.get("basic_only", [])]
        if identity
    }
    basic_scenario_by_id = {
        scenario_item.get("id", ""): scenario_item
        for scenario_item in (basic_scenarios or [])
        if scenario_item.get("id")
    }
    feature_paths = [
        tag["name"][6:] for tag in feature.get("tags", []) if tag["name"].startswith("@path-")
    ]
    total_groups = 0
    for child in feature["children"]:
        if "background" in child:
            raise ValueError("Write prerequisites inside each TC; Background is not allowed")
        scenario = child["scenario"]
        tags = [tag["name"] for tag in scenario["tags"]]
        tc_ids = [tag[1:] for tag in tags if tag.startswith("@TC-")]
        if len(tc_ids) != 1 or not re.fullmatch(r"TC-\d{3,}", tc_ids[0]):
            raise ValueError("Each TC must have one numeric identity, e.g. @TC-022")
        identity = tc_ids[0]
        number = int(identity[3:])
        if number <= 0 or identity != f"TC-{number:03d}" or number in identities:
            raise ValueError(f"Duplicate or noncanonical TC identity: {identity}")
        identities.add(number)
        paths = [tag[6:] for tag in tags if tag.startswith("@path-")] or feature_paths
        if len(paths) != 1:
            raise ValueError(f"Specify one Feature or Scenario @path- tag: {identity}")
        path = [unquote(label) for label in paths[0].split("/")]
        if functions_root:
            if identity in basic_scenario_by_id:
                job_scenario = basic_scenario_by_id[identity]
                path = ["Basic Scenarios", job_scenario.get("job", "Job"), job_scenario.get("title", "Scenario")]
            elif identity in basic_only_ids:
                path = ["Basic Scenarios", "Job Scenario"]
            else:
                path.insert(0, "Functions")
        if any(not label.strip() for label in path):
            raise ValueError(f"Empty tree path segment: {identity}")
        tc_label = identity
        tc_path = " > ".join(path)
        title = scenario["name"]
        for prefix in (identity, identity.removeprefix("TC-")):
            if title.startswith(prefix + " "):
                title = title[len(prefix) + 1 :]
                break
        prerequisites, groups, phase = [], [], "precondition"
        for step in scenario["steps"]:
            keyword = step["keyword"].strip()
            if keyword == "When":
                groups.append([[], []])
                phase = "action"
            elif keyword == "Then":
                phase = "expected"
            if phase == "precondition":
                prerequisites.append((step["text"], step.get("docString", {}).get("content", "")))
            else:
                if phase == "expected" and normalize_expected_result(step["text"]) != step["text"]:
                    raise ValueError(f"TC up dictionary violation: {identity}: {step['text']}")
                groups[-1][0 if phase == "action" else 1].append(step["text"])
        rows = []
        for number, (actions, expected) in enumerate(groups, 1):
            if not actions or not expected:
                raise ValueError(f"Missing Steps / Expected Result: {identity}, {number}")
            action_list = "<ol>" + "".join(f"<li>{escape(a)}</li>" for a in actions) + "</ol>"
            result = "<br>".join(escape(item) for item in expected)
            rows.append(f"<tr><td>{number}</td><td>{action_list}</td><td>{result}</td></tr>")
        total_groups += len(groups)
        pending = "@requires-specification" in tags
        specifications = [label for tag, label in SPECIFICATION_LABELS.items() if tag in tags]
        if pending and not specifications:
            specifications = ["요구사항 미확정"]
        review_tags = [tag for tag in tags if tag.startswith("@review-")]
        if len(review_tags) > 1 or any(
            tag not in ("@review-to_review", "@review-reviewed") for tag in review_tags
        ):
            raise ValueError(f"Invalid review state: {identity}")
        if review_tags and review_tags[0] == "@review-reviewed":
            specifications = [
                "검수 완료" if review_tags[0] == "@review-reviewed" else "검수 대기"
            ] + specifications
        chips_html = (
            '<div class="tc-chips">'
            + "".join(
                f'<span class="badge {chip_class(label)}">{escape(label)}</span>'
                for label in specifications
            )
            + "</div>"
            if specifications
            else ""
        )
        prerequisites_html = (
            '<h3>Pre-condition</h3><div class="table-wrap"><table class="preconditions">'
            + '<thead><tr><th scope="col">No.</th><th scope="col">Steps</th></tr></thead><tbody>'
            + "".join(
                f"<tr><td>{number}</td><td><strong>{escape(title)}</strong>"
                + f'<div class="precondition-details">{escape(details)}</div></td></tr>'
                for number, (title, details) in enumerate(prerequisites, 1)
            )
            + "</tbody></table></div>"
            if prerequisites
            else ""
        )
        cards.append(
            f'<article class="tc" id="{escape(identity, quote=True)}">'
            f'<div class="tc-heading"><div class="tc-title">'
            f'<div class="tc-meta">{escape(tc_path)}</div>'
            f'<div class="tc-title-line"><h2><span class="tc-id">{escape(tc_label)}</span> {escape(title)}</h2>'
            + chips_html
            + "</div></div></div>"
            + prerequisites_html
            + '<div class="table-wrap"><table><thead><tr><th>No.</th><th>Steps</th>'
            + "<th>Expected Result</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table></div></article>"
        )
        kind = next((tag[6:] for tag in tags if tag.startswith("@type-")), "other")
        title = scenario["name"].removeprefix(identity + " ")
        navigation.append(
            {
                "id": identity,
                "title": title,
                "kind": kind,
                "pending": pending,
                "specifications": specifications,
                "path": ["Functions"] if functions_root and identity not in basic_only_ids else path,
                "flat": functions_root and identity not in basic_only_ids,
                "tree_title": (
                    f'{identity} {" / ".join(path[1:])} — {title}'
                    if functions_root and identity not in basic_only_ids
                    else title
                ),
            }
        )
    all_function_entries = {entry["id"]: entry for entry in navigation}
    navigation = [entry for entry in navigation if entry["id"] not in basic_only_ids]
    function_tc_count = len(navigation)
    if basic_scenarios:
        function_ids = set(all_function_entries)
        scenario_ids = set()
        for scenario in basic_scenarios:
            identity = scenario.get("id", "")
            title = scenario.get("title", "")
            if not re.fullmatch(r"TC-\d{3,}", identity) or identity in scenario_ids:
                raise ValueError(f"Invalid or duplicate Basic Scenario TC identity: {identity}")
            if identity not in function_ids or identity not in basic_only_ids:
                raise ValueError(f"Basic Scenario must be a Basic-only TC in the Gherkin source: {identity}")
            scenario_ids.add(identity)
            refs = scenario.get("steps", [])
            if not refs or any(ref not in function_ids for ref in refs):
                raise ValueError(f"Unknown or empty Function references in {identity}")
            if not title or identity in refs:
                raise ValueError(f"Basic Scenario requires a title and distinct ordered TC references: {identity}")
            scenario_path = ["Basic Scenarios", scenario.get("job", "Job"), title]
            navigation.append({
                **all_function_entries[identity],
                "path": scenario_path,
                "tree_title": title,
                "flat": False,
                "force_tc_id": True,
            })
            for ref in refs:
                navigation.append({
                    **all_function_entries[ref],
                    "path": scenario_path,
                    "tree_title": all_function_entries[ref]["title"].split(" — ", 1)[-1],
                    "flat": False,
                    "force_tc_id": True,
                })
        referenced_steps = {
            ref for scenario in basic_scenarios for ref in scenario.get("steps", [])
        }
        if basic_only_ids - (referenced_steps | scenario_ids):
            raise ValueError(
                f"Basic-only TCs are not referenced by a Basic Scenario: "
                f"{sorted(basic_only_ids - referenced_steps)}"
            )
    navigation_html = render_navigation(navigation)
    present_types = {entry["kind"] for entry in navigation}
    legend_items = "".join(
        f'<div class="legend-item"><span class="badge">{escape(label)}</span>'
        f"<span>{escape(TYPE_DESCRIPTIONS[kind])}</span></div>"
        for kind, label in TYPE_LABELS.items()
        if kind in present_types
    )
    document = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TC 검수</title><style>{STYLE}</style></head><body>
<header><div class="tree-heading masthead"><h1 class="review-heading">TC 검수</h1><div class="tree-actions"><button id="theme-toggle" type="button" aria-pressed="false">&#45796;&#53356; &#47784;&#46300;</button></div></div>
<p>{function_tc_count}개 Function TC · {len(basic_only_ids)}개 Basic 전용 TC · {len(basic_scenarios or [])}개 Basic Scenario · {total_groups}개 Function Step 묶음 · 실행 결과 없음</p></header>
<div class="toolbar"><input id="search" type="text" aria-label="TC 검색 표현식" autocomplete="off" autofocus placeholder="TC 검색: 예) 버튼 !검수 | 저장" title="공백 AND · !제외 · | OR · ^접두 · 접미$ · '정확 포함">
<span id="count" role="status" aria-live="polite"></span></div>
<div class="layout"><aside class="tree-panel"><div class="tree-heading"><h2 id="tc-tree-title" class="review-heading">TC 검수 스위트</h2><div class="tree-actions" aria-label="Suite expansion controls"><button id="tree-collapse-tcs" type="button" title="Collapse TC nodes">&#45432;&#46300;&#47564; &#51217;&#44592;</button><button id="tree-expand-all" type="button" title="Expand every suite">&#47784;&#46160; &#54204;&#52824;&#44592;</button></div></div><nav id="tc-tree" aria-labelledby="tc-tree-title">{navigation_html}</nav></aside><div id="tree-resizer" class="tree-resizer" role="separator" tabindex="0" aria-label="TC 트리 폭 조절" aria-orientation="vertical" aria-controls="tc-tree" aria-valuemin="240" aria-valuenow="350" title="드래그 또는 좌우 방향키로 폭 조절"></div><main>
<h2 class="review-heading">TC 검수 본문</h2>
<p id="empty" class="empty" hidden>검색 결과가 없습니다.</p><div id="results">{"".join(cards)}</div>
<section class="intro"><h2>검수 범위</h2><ul>
<li>TC 초안 검수. 실제 실행·자동화 없음.</li>
<li>미관찰 입력요소: 추가 확인 필요.</li>
<li><span class="badge pending">SQA 확인요소 · 색상 chip</span>: PASS/FAIL 기준 미확정. 값·범위·동작 확정 후 검증.</li>
</ul><h3 id="ui-legend-title">UI 유형</h3><div class="legend-items" aria-labelledby="ui-legend-title">{legend_items}</div></section>
</main></div><script>{SCRIPT}</script></body></html>"""
    return document, {
        "tc_count": function_tc_count,
        "basic_only_tc_count": len(basic_only_ids),
        "basic_scenario_count": len(basic_scenarios or []),
        "step_groups": total_groups,
    }


def load_basic_scenarios() -> list[dict]:
    scenario_file = hpe990_folders.D_HPE990_CONFIGS / "basic_scenarios.json"
    return json.loads(scenario_file.read_text(encoding="utf-8"))


def main():
    from cores.hpe990.functions.tc_repository import load_review_source

    source = load_review_source()
    document, summary = render_review(source, load_basic_scenarios(), functions_root=True)
    output = hpe990_folders.D_HPE990_EVIDENCE / "093ca349/preferences-general-tc-review.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print({"html": str(output), **summary})


if __name__ == "__main__":
    main()
