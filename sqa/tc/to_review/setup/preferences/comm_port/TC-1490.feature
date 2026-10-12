@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Comm.%20Port
Feature: Edger > Setup > Preferences > Comm. Port 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
  @TC-1490 @type-navigation
  Scenario: TC-1490 Comm. Port 화면 진입 및 수집 요소 확인
    # Step 1
    When Setup > Preferences > Comm. Port 탭 선택
    And Comm. Port 설정 영역 상단부터 하단까지 스크롤
    Then Preferences 창의 Comm. Port 탭이 선택 상태로 보여야 합니다.
    And 스크롤 영역은 각 요소 위치에 도달했을 때 해당 요소가 보여야 합니다.
    And 하기 수집 요소가 각각 보여야 합니다.
    And BARCODE
    And BARCODE > Baud Rate
    And TRACER
    And TRACER > Protocol
    And TRACER > Baud Rate
    And BLOCKER
    And BLOCKER > Protocol
    And BLOCKER > Baud Rate
    And Job Request > Job Request Port
    And Job Request > Delete Existing Job Before Requesting
    And DCS / VCA Options > Machine ID
    And DCS / VCA Options > The Number of Radii
    And DCS / VCA Options > Radius Mode
    And DCS / VCA Options > Format
    And DCS / VCA Options > Packet Timeout (sec)
    And DCS / VCA Options > Confirmation Timeout (sec)
    And Save
    And Cancel
