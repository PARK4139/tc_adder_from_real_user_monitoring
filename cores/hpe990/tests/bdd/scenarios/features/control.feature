@ISSUE-5488b646 @AC-automated-control-with-concurrent-ram
Feature: Keep observing when automated control fails
  Scenario: A rejected control request preserves monitoring and owned-session cleanup
    Given the approved Emulator is stopped
    When I launch the Emulator and continue into Edger
    And I request an unavailable control
    And I stop the owned Emulator application explicitly
    Then the rejected request and cleanup remain in the monitoring evidence
