@ISSUE-50c688e3 @AC-bdd-scenario-list
Feature: Browse registered BDD scenarios
  Scenario: Registered scenarios are available without the UI gallery
    Given the approved Emulator is stopped
    When I launch the Emulator and continue into Edger
    And I open the BDD scenario screen
    Then the viewer lists every registered BDD scenario with its steps and issue
    When I open Setup and its Shutdown confirmation
    And I cancel the Shutdown confirmation
    And I stop the owned Emulator application explicitly
    Then every declared observed activity has session-linked monitoring evidence
