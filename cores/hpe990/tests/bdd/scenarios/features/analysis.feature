@ISSUE-f797f6a4 @AC-evidenced-state-transition-mapping
Feature: Understand the observed Emulator workflow
  Scenario: Every observed state and transition has traceable evidence
    Given the approved Emulator is stopped
    When I launch the Emulator and continue into Edger
    And I open Setup and its Shutdown confirmation
    And I cancel the Shutdown confirmation
    And I stop the owned Emulator application explicitly
    Then the analysis maps every observed state and transition to evidence
