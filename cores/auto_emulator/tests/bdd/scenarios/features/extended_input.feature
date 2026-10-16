@ISSUE-f182f260 @AC-keyboard-shortcuts @ISSUE-955a2810 @AC-ocr-element-control @ISSUE-fea44e48 @AC-foreground-activation
Feature: Recollected visual input and native keyboard delivery
  Scenario: OCR Preferences entry and reversible keyboard tab navigation three times
    Given Setup is open with an unchanged owned Emulator and active Real Activity Monitoring
    When I enter Preferences through its recollected OCR label and navigate tabs three times
    Then every observed tab transition matches the requested keyboard input and Real Activity Monitoring remains active
