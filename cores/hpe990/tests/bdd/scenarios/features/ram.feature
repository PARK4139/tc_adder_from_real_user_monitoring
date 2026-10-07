@ISSUE-92dd1b63 @AC-observed-activity-session-coverage
Feature: Observe Emulator activity throughout its session
  Scenario: Startup, modal navigation and application stop remain monitored
    Given the approved Emulator is stopped
    When I launch the Emulator and continue into Edger
    And I open Setup and its Shutdown confirmation
    And I cancel the Shutdown confirmation
    And I stop the owned Emulator application explicitly
    Then every declared observed activity has session-linked monitoring evidence
