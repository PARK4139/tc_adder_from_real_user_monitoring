@draft @ISSUE-66c80f85 @AC-preferences-tabs-review @path-Edger/Setup/Preferences/Edging
Feature: Edger > Setup > Preferences > Edging 검수 TC

# MCP 수집 근거: {D_TEMP}/hpe990/evidence/66c80f85/collection-report.json
# 화면 표시 관찰과 TC 실행 판정은 별개. 본 TC는 미실행 초안.
  @TC-500 @type-navigation
  Scenario: TC-500 Edging 화면 진입 및 수집 요소 확인
    # Step 1
    When Setup > Preferences > Edging 탭 선택
    And Edging 설정 영역 상단부터 하단까지 스크롤
    Then Preferences 창의 Edging 탭이 선택 상태로 보여야 합니다.
    And 스크롤 영역은 각 요소 위치에 도달했을 때 해당 요소가 보여야 합니다.
    And 하기 수집 요소가 각각 보여야 합니다.
    And Edging Start Side
    And Default Lens Material
    And Safety Mode
    And Default Drill Quality Mode
    And Edging Type > Frame (Metal)
    And Edging Type > Frame (Soft Plastic)
    And Edging Type > Frame (Hard Plastic)
    And Edging Type > Pattern
    And Bevel Options > Default Bevel Position
    And Bevel Options > Default Value > Percent (%)
    And Bevel Options > Default Value > Front (mm)
    And Bevel Options > Default Value > Rear (mm)
    And Bevel Options > Default Value > Basecurve
    And Bevel Options > Blunt Bevel Amount > Small
    And Bevel Options > Blunt Bevel Amount > Large
    And Bevel Options > Step Bevel Blunt Bevel Amount > Small
    And Bevel Options > Step Bevel Blunt Bevel Amount > Large
    And Bevel Options > Safety Beveling (Front)
    And Bevel Options > Safety Beveling (Rear)
    And Rimless Options > Default Groove Position
    And Rimless Options > Default Value > Percent (%)
    And Rimless Options > Default Value > Front (mm)
    And Rimless Options > Default Value > Rear (mm)
    And Rimless Options > Default Value > Basecurve
    And Rimless Options > Default Value > Groove Width
    And Rimless Options > Default Value > Groove Depth
    And Rimless Options > Add Polishing
    And Rimless Options > Safety Beveling (Front)
    And Rimless Options > Safety Beveling (Rear)
    And Safety Bevel Amount > Front
    And Safety Bevel Amount > Rear Small
    And Safety Bevel Amount > Rear Large
    And Asymmetric Bevel Default Value > Front Height
    And Asymmetric Bevel Default Value > Rear Height
    And Mini Bevel Default Value > Height
    And Mini Bevel Default Value > Size Offset
    And Semi-U Bevel Default Value > Front Width
    And Semi-U Bevel Default Value > Rear Height
    And Step Bevel Default Value > Front Width
    And Step Bevel Default Value > Top Value
    And Step Bevel Default Value > Bottom Value
    And Step Bevel Default Value > Temporal Value
    And Step Bevel Default Value > Nasal Value
    And Feeling Outside Of Bevel
    And Feeling After Roughing
    And Pre-Roughing (PC/TR)
    And Manual Position UI > Default Region (Clock position)
    And Manual Position UI > Angle Guideline
    And Manual Position UI > Tilt Mode
    And Default Roughing Mode > PL/HI
    And Default Roughing Mode > PC/TR
    And Default Roughing Mode > Apply default roughing mode when lens material changed
    And Default Roughing Mode > Spiral/Axial Roughing Safety Mode
    And Hydrophobic Mode > Hydrophobic Mode
    And Hydrophobic Mode > Default Value > Roughing Mode
    And Hydrophobic Mode > Default Value > Safety Mode
    And Hydrophobic Mode > Default Value > Rotation Speed (%)
    And Hydrophobic Mode > Default Value > Optical Center Clamp Pressure
    And Hydrophobic Mode > Default Value > Box Center Clamp Pressure
    And Save
    And Cancel
