# 검수 Suite 구성

Suite는 실제 화면·탭 이름과 기능 묶음을 혼합합니다.
정본 기준은 [suite_hierarchy.py](../../rules/scenarios/suite_hierarchy.py)이며,
각 TC의 `@path-...` 태그가 검수 웹 트리를 결정합니다.

```text
HPE990 / 1.22
└─ Edger
   ├─ Setup
   │  └─ Preferences
   │     ├─ General
   │     │  ├─ Sleep Mode               TC-060~TC-090
   │     │  └─ Message Box Font Size    TC-170~TC-190
   │     ├─ Layout
   │     ├─ Edging
   │     ├─ Digital Pattern
   │     ├─ Hole Editor
   │     ├─ Frame Fitting
   │     └─ Comm. Port
   └─ 작업 불러오기
      ├─ TC-250 작업 미선택 상태의 UI 확인
      ├─ Job Manager
      │  ├─ TC-260 Job Manager 진입 및 설치 샘플 목록 확인
      │  └─ TC-270 CIRCLE 샘플 선택 및 작업 불러오기
      └─ TC-280 작업 불러오기 후 주요 UI 활성화 확인
```

`작업 불러오기`는 검수 기능 분류이며 실제 UI 메뉴명이 아닙니다.
단일 TC를 위한 초기 상태·활성화 하위 폴더는 만들지 않습니다.
Job Editor, Digital Pattern, Hole Editor는 이번 TC의 Steps에 포함되며,
독립 검수 TC가 추가되기 전에는 빈 Suite로 표시하지 않습니다.

기존 24개 TC의 ID·제목·사전조건·Steps·Expected Result는 유지했습니다.
기본 신규 발급은 10 단위이며 이번 추가 ID는 TC-250~TC-280입니다.
작성된 시나리오는 초안으로, 이 변경에서 자동화 시험을 실행한 결과가 아닙니다.

[공유 검수 웹](http://172.20.13.185:9999/tc-up-validation/)은 TC 파일과 경로 변경을
서버 재시작 없이 반영합니다. 파일의 Suite 경로와 실제 Steps의 조작 경로를 구분합니다.
