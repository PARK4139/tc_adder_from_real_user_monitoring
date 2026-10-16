@ISSUE-04be9d05 @AC-drag-control
Feature: Native UI-ID drag stays monitored and its application result is verified

  Scenario: General scrollbar drag and reverse restore the viewport three times
    Given General is open at its initial scroll position with Real Activity Monitoring active
    When I drag the native scrollbar and reverse it three times through MCP
    Then each drag scrolls General and each reverse restores its initial position
    And invalid drag targets and parameters are rejected while Real Activity Monitoring stays active
