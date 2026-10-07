@ISSUE-093ca349 @AC-required-launch-to-exit-transitions
Feature: Complete the observed Emulator session
  Scenario: Launch through Continue, navigate a confirmation and stop the application
    Given the approved Emulator is stopped
    When I launch the Emulator and continue into Edger
    And I open Setup and its Shutdown confirmation
    And I cancel the Shutdown confirmation
    And I stop the owned Emulator application explicitly
    Then the observed workflow is linked to every required scenario step
