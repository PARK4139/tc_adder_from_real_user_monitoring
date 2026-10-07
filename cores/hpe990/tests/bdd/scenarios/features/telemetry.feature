@ISSUE-4c1abd34 @AC-versioned-window-change-events
Feature: Retain changes to the Emulator window locally
  Scenario: Observed window changes have ordered and correlated evidence
    Given the approved Emulator is stopped
    When I launch the Emulator and continue into Edger
    And I change and restore the main window geometry
    And I change and restore the job category selection
    And I open Setup and its Shutdown confirmation
    And I cancel the Shutdown confirmation
    And I stop the owned Emulator application explicitly
    Then observed reference changes have valid ordered local telemetry
