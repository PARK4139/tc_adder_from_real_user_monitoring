"""Export authored Gherkin drafts as numbered TC tables for human review."""

import re
from html import escape
from urllib.parse import unquote

from gherkin.parser import Parser

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.tc_wording import normalize_expected_result

TEST_TARGET = {
    "model": "HPE990",
    "version": "1.22",
    "executable": "HPE990_v1.22_251010.exe",
}

STYLE = """
:root{font-family:'Segoe UI','Malgun Gothic',sans-serif;color:#20334a;background:#f3f6fa}
*{box-sizing:border-box}[hidden]{display:none!important}body{margin:0}header{background:#172e48;color:white;padding:28px 32px}
h1{font-size:25px;margin:0 0 10px}header p{margin:0;color:#c7d8ec;font-size:14px}
.toolbar{display:flex;gap:12px;align-items:center;padding:18px 30px;flex-wrap:wrap;position:sticky;top:0;background:#f3f6fa;z-index:2}
input{font:inherit;padding:10px 14px;border:1px solid #c5d3e2;border-radius:7px;background:white;min-width:240px;flex:1}#count{font-size:13px;color:#536f8b}
.layout{display:grid;grid-template-columns:var(--tree-width,350px) 10px minmax(0,1fr);gap:8px;padding:0 30px 32px}
.tree-resizer{position:sticky;top:82px;align-self:start;height:82vh;cursor:col-resize;touch-action:none;border-radius:5px;display:flex;justify-content:center}.tree-resizer:before{content:"";width:3px;background:#ccd9e6;border-radius:3px}.tree-resizer:hover:before,.tree-resizer:focus-visible:before{background:#3074bd}.tree-resizer:focus-visible{outline:2px solid #3074bd;outline-offset:2px}body.resizing-tree{cursor:col-resize;user-select:none}
.tree-panel{position:sticky;top:82px;align-self:start;min-width:0}nav{max-height:calc(82vh - 54px);overflow:auto;background:white;border:1px solid #dae4ee;border-radius:10px;padding:12px}

.review-heading{font-size:18px;margin:0 0 16px;padding:4px 0 12px;border-bottom:1px solid #dae4ee}
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
@media(max-width:900px){.layout{grid-template-columns:1fr;padding:0 14px 20px}.tree-resizer{display:none}.tree-panel{position:static}nav{max-height:200px}.toolbar{padding:14px}article{padding:14px}}
@media print{body{background:white}header{background:white;color:black;padding:0 0 16px}header p{color:#444}.toolbar,.tree-panel,.tree-resizer{display:none}.layout{display:block;padding:0}article,.intro{border:0;padding:0}.tc{display:block!important}table{font-size:11px}tr{break-inside:avoid}h2{break-after:avoid}.empty{display:none}}
"""

SCRIPT = r"""
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
const search=document.getElementById('search'),cards=[...document.querySelectorAll('.tc')];
const normalize=text=>text.normalize('NFKC').toLowerCase().replace(/\s+/g,' ').trim();
function fuzzyScore(query,text){
 if(!query)return 0;
 let cursor=0,previous=-2,score=0;
 for(const letter of query){
  const index=text.indexOf(letter,cursor);if(index<0)return null;
  score+=index===previous+1?8:3;
  if(index===0||/[\s_\-/>()]/.test(text[index-1]))score+=4;
  previous=index;cursor=index+letter.length;
 }
 if(text.startsWith(query))score+=20;
 if(text.includes(query))score+=20;
 return score-text.length/20;
}
const records=cards.map((card,index)=>({card,index,
 link:document.querySelector('nav a[href="#'+card.id+'"]'),
 title:normalize(card.querySelector('h2').textContent.replace(card.id,'')),
 fields:[normalize(card.id),...[...card.querySelectorAll('h2,.tc-meta,li,td,.precondition-details')].map(element=>normalize(element.textContent.replace(card.id,'')))]}));
const branches=[...document.querySelectorAll("nav details")];
const containers=[...document.querySelectorAll(".tree-children")].map(node=>({node,children:[...node.children]}));
const highlights=[];
document.querySelectorAll("nav .tree-title,nav .tree-id,nav .tree-label").forEach(node=>highlights.push({node,text:node.textContent}));
for(const card of cards){
 const walker=document.createTreeWalker(card,NodeFilter.SHOW_TEXT),texts=[];
 while(walker.nextNode())if(walker.currentNode.textContent.trim())texts.push(walker.currentNode);
 for(const text of texts){const node=document.createElement("span");text.replaceWith(node);node.textContent=text.textContent;highlights.push({node,text:text.textContent});}
}
function highlight(node,text,terms){
 if(!terms.length){node.textContent=text;return;}
 const chars=Array.from(text),folded=[],mapping=[],marked=new Set();
 chars.forEach((char,index)=>Array.from(char.normalize("NFKC").toLowerCase()).forEach(letter=>{folded.push(letter);mapping.push(index)}));
 for(const term of terms){let cursor=0,positions=[];
  for(const letter of term){const index=folded.indexOf(letter,cursor);if(index<0){positions=[];break;}positions.push(mapping[index]);cursor=index+1;}
  positions.forEach(index=>marked.add(index));
 }
 if(!marked.size){node.textContent=text;return;}
 const fragment=document.createDocumentFragment();let buffer="",last=false;
 function flush(){if(!buffer)return;const part=last?document.createElement("mark"):document.createTextNode("");part.textContent=buffer;fragment.append(part);buffer="";}
 chars.forEach((char,index)=>{const active=marked.has(index);if(active!==last){flush();last=active;}buffer+=char;});flush();node.replaceChildren(fragment);
}
try{const saved=JSON.parse(sessionStorage.getItem("tc-review-tree-open")||"{}");branches.forEach(node=>{if(node.dataset.node in saved)node.open=saved[node.dataset.node];});}catch{}
branches.forEach(node=>node.addEventListener("toggle",()=>{
 if(!search.value.trim())sessionStorage.setItem("tc-review-tree-open",JSON.stringify(Object.fromEntries(branches.map(branch=>[branch.dataset.node,branch.open]))));
}));
let matches=[],selected=0,searching=false,previousOpen=new Map();
function reveal(link){let parent=link.parentElement;while(parent){if(parent.tagName==="DETAILS")parent.open=true;parent=parent.parentElement;}}
function selectResult(index){
 selected=Math.max(0,Math.min(index,matches.length-1));
 records.forEach(record=>record.link.removeAttribute('aria-current'));
 if(matches.length){matches[selected].link.setAttribute('aria-current','true');reveal(matches[selected].link);}
}
function filter(){
 const terms=normalize(search.value).split(' ').filter(Boolean);
 const active=matches[selected]?.card.id;
 if(terms.length&&!searching)previousOpen=new Map(branches.map(node=>[node,node.open]));
 matches=[];
 for(const record of records){
  let score=0,show=true;
  for(const term of terms){
   const titleScore=fuzzyScore(term,record.title);
   const scores=record.fields.map(field=>fuzzyScore(term,field)).filter(value=>value!==null);
   if(!scores.length){show=false;break;}
   score+=titleScore===null?Math.max(...scores):titleScore+100;
  }
  record.card.hidden=record.link.hidden=!show;
  if(show)matches.push({...record,score});
 }
 matches.sort((a,b)=>b.score-a.score||a.index-b.index);
 const ordered=[...matches,...records.filter(record=>record.card.hidden)];
 const cardFragment=document.createDocumentFragment();ordered.forEach(record=>cardFragment.append(record.card));document.getElementById('results').append(cardFragment);
 const scores=new Map(matches.map(record=>[record.link,record.score]));
 function best(node){const links=node.tagName==="A"?[node]:[...node.querySelectorAll("a")];return Math.max(-Infinity,...links.map(link=>scores.get(link)??-Infinity));}
 containers.forEach(({node,children})=>{const sorted=terms.length?[...children].sort((a,b)=>{const left=best(a),right=best(b);return left===right?0:right-left;}):children;node.append(...sorted);});
 [...branches].reverse().forEach(node=>{const total=node.querySelectorAll("a").length,count=node.querySelectorAll("a:not([hidden])").length;node.hidden=count===0;node.querySelector(":scope > summary .tree-count").textContent=total+"개";if(terms.length&&count)node.open=true;else if(!terms.length&&searching)node.open=previousOpen.get(node)??node.open;});
 highlights.forEach(({node,text})=>highlight(node,text,terms));
 document.getElementById('count').textContent=matches.length+' / '+cards.length+'개 TC';
 document.getElementById('empty').hidden=matches.length>0;
 searching=terms.length>0;
 const hash=location.hash.slice(1),preferred=matches.findIndex(record=>record.card.id===(hash||active));
 selectResult(preferred<0?0:preferred);
}
records.forEach(record=>record.link.addEventListener("click",()=>{const index=matches.findIndex(item=>item.card.id===record.card.id);if(index>=0)selectResult(index);}));
window.addEventListener("hashchange",()=>{const index=matches.findIndex(record=>record.card.id===location.hash.slice(1));if(index>=0)selectResult(index);});
search.addEventListener('input',filter);
search.addEventListener('keydown',event=>{
 if(event.isComposing)return;
 if(event.key==='ArrowDown'||event.key==='ArrowUp'){
  event.preventDefault();selectResult(selected+(event.key==='ArrowDown'?1:-1));
  if(matches.length)matches[selected].link.scrollIntoView({block:'nearest'});
 }else if(event.key==='Enter'&&matches.length){event.preventDefault();matches[selected].link.click();}
});
filter();
"""


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
    root = {"children": {}, "entries": []}
    for entry in entries:
        node = root
        target = entry.get("test_target", TEST_TARGET)
        for label in (target["model"], target["version"], *entry["path"]):
            node = node["children"].setdefault(label, {"children": {}, "entries": []})
        node["entries"].append(entry)

    def leaf(entry, label):
        identity = escape(entry["id"], quote=True)
        labels = entry.get("specifications", ["요구사항 미확정"] if entry["pending"] else [])
        chip = (
            '<span class="tree-chips">'
            + "".join(
                f'<span class="tree-chip {"actual" if label == ACTUAL_BEHAVIOR_LABEL else "pending"}">{escape(label)}</span>'
                for label in labels
            )
            + "</span>"
            if labels
            else ""
        )
        return (
            f'<a href="#{identity}" title="{escape(entry["title"], quote=True)}">'
            f'<span class="tree-leaf-top"><span class="tree-id">{escape(entry["id"])}</span>'
            f'<span class="tree-title">{escape(label)}</span>{chip}</span></a>'
        )

    def branch(label, contents, key):
        count = contents.count('<a href="')
        return (
            f'<details open data-node="{escape(key, quote=True)}"><summary>'
            f'<span class="tree-label">{escape(label)}</span><span class="tree-count">{count}개</span></summary>'
            f'<div class="tree-children">{contents}</div></details>'
        )

    def render(node, key=""):
        parts = [
            branch(label, render(child, key + "/" + label), key + "/" + label)
            for label, child in node["children"].items()
        ]
        parts.extend(leaf(entry, entry["title"]) for entry in node["entries"])
        return "".join(parts)

    return render(root)


def render_review(source: str) -> tuple[str, dict]:
    feature = Parser().parse(source)["feature"]
    cards, navigation = [], []
    identities = set()
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
        chips_html = (
            '<div class="tc-chips">'
            + "".join(
                f'<span class="badge {"actual" if label == ACTUAL_BEHAVIOR_LABEL else "pending"}">{escape(label)}</span>'
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
                "path": path,
            }
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
<header><h1>TC 검수</h1>
<p>{len(cards)}개 TC · {total_groups}개 Step 묶음 · 시나리오 작성 초안 · 실행 결과 없음</p></header>
<div class="toolbar"><input id="search" type="text" aria-label="TC 퍼지 검색" autocomplete="off" autofocus placeholder="TC 검색기">
<span id="count" role="status" aria-live="polite"></span></div>
<div class="layout"><aside class="tree-panel"><h2 id="tc-tree-title" class="review-heading">TC 검수 스위트</h2><nav id="tc-tree" aria-labelledby="tc-tree-title">{navigation_html}</nav></aside><div id="tree-resizer" class="tree-resizer" role="separator" tabindex="0" aria-label="TC 트리 폭 조절" aria-orientation="vertical" aria-controls="tc-tree" aria-valuemin="240" aria-valuenow="350" title="드래그 또는 좌우 방향키로 폭 조절"></div><main>
<h2 class="review-heading">TC 검수 본문</h2>
<p id="empty" class="empty" hidden>검색 결과가 없습니다.</p><div id="results">{"".join(cards)}</div>
<section class="intro"><h2>검수 범위</h2><ul>
<li>TC 초안 검수. 실제 실행·자동화 없음.</li>
<li>미관찰 입력요소: 추가 확인 필요.</li>
<li><span class="badge pending">SQA 확인요소 · 색상 chip</span>: PASS/FAIL 기준 미확정. 값·범위·동작 확정 후 검증.</li>
</ul><h3 id="ui-legend-title">UI 유형</h3><div class="legend-items" aria-labelledby="ui-legend-title">{legend_items}</div></section>
</main></div><script>{SCRIPT}</script></body></html>"""
    return document, {"tc_count": len(cards), "step_groups": total_groups}


def main():
    from cores.hpe990.functions.tc_repository import load_review_source

    document, summary = render_review(load_review_source())
    output = hpe990_folders.D_HPE990_EVIDENCE / "093ca349/preferences-general-tc-review.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print({"html": str(output), **summary})


if __name__ == "__main__":
    main()
