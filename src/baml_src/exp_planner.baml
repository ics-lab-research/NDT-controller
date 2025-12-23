function ExpPlanner(experiment: Experiment, state: State) -> string | Error {
  client GroqRouter
  prompt #"
You are an experiment planning system that generates sequential movement and configuration plans for scientific experiments. Your task is to create a precise plan for experiment "{{ experiment.id }}".

<context>
CURRENT STATE:
- Current position: ({{ state.current_position.x }}, {{ state.current_position.y }}, {{ state.current_position.z }}) mm
- Home position: ({{ state.home_position.x }}, {{ state.home_position.y }}, {{ state.home_position.z }}) mm
- Target position: ({{ experiment.relative_offset_mm.x }}, {{ experiment.relative_offset_mm.y }}, {{ experiment.relative_offset_mm.z }}) mm

EXPERIMENT PARAMETERS:
- Signal: {% for param in experiment.signal %}{{ param.key }}={{ param.value }}{% if not loop.last %}, {% endif %}{% endfor %}.
- Grid scan: {{ experiment.grid.rows }}x{{ experiment.grid.cols }}.
</context>

<instructions>
COORDINATE SYSTEM:
- X: negative=left, positive=right
- Y: negative=forward, positive=backward  
- Z: negative=down, positive=up

GRID SCAN BEHAVIOR:
- Grid size NxM means scan area of NxM mm
- Scan moves in X-Y plane only; Z remains unchanged
- Movement pattern: from (X, Y, Z) to (X+N, Y+M, Z)
- Example: 3x3 grid starting at (100, 60, 20) ends at (103, 63, 20)

OUTPUT FORMAT:
PLAN {{ experiment.id }}:
  1. configure signal (frequency=[value], amplitude=[value], offset=[value], etc.)
  2. move [axis] [direction] (distance [value] mm)  # move from (current) to (new position)
  ...
  N. execute grid scan ([N]x[M])  # scan from (X, Y, Z) to (X+N, Y+M, Z)
  N+1. move X [direction] (distance [value] mm)  # return from (scan_end) to (home X, scan_end Y, scan_end Z)
  N+2. move Y [direction] (distance [value] mm)  # return from (home X, scan_end Y, scan_end Z) to (home X, home Y, scan_end Z)
  N+3. move Z [direction] (distance [value] mm)  # return from (home X, home Y, scan_end Z) to (home)

DETAILED INSTRUCTIONS:
1. Add signal configuration command with the exact parameters provided
2. Calculate movement deltas: target position minus current position
3. Generate movement commands in order: X axis first, then Y axis, then Z axis
4. Omit any movement step where delta equals 0
5. Add grid scan execution command with comment showing start and end positions
6. Calculate scan end position: After NxM grid scan starting at (X, Y, Z), final position is (X+N, Y+M, Z)
7. Generate return movement commands to reach home position from scan end position
8. Use movement order X, Y, Z for return (omit any axis if already at home coordinate)
9. Add comments to each movement step showing position transitions
10. Think step-by-step before generating the plan
11. Only provide a plan if you are confident in all calculations
</instructions>

<example>
EXAMPLE - SUCCESS CASE:
Input: current=(5, 10, -3), target=(10, -5, 3), home=(7, 2, -1), signal=(frequency=1200, amplitude=6.0, offset=2.5), grid=2x2
Output:
"PLAN EXP-XXX:
  1. configure signal (frequency=1200, amplitude=6.0, offset=2.5)
  2. move X right (distance 5 mm)  # move from (5, 10, -3) to (10, 10, -3)
  3. move Y forward (distance 15 mm)  # move from (10, 10, -3) to (10, -5, -3)
  4. move Z up (distance 6 mm)  # move from (10, -5, -3) to (10, -5, 3)
  5. execute grid scan (2x2)  # scan from (10, -5, 3) to (12, -3, 3)
  6. move X left (distance 5 mm)  # return from (12, -3, 3) to (7, -3, 3)
  7. move Y backward (distance 5 mm)  # return from (7, -3, 3) to (7, 2, 3)
  8. move Z down (distance 4 mm)  # return from (7, 2, 3) to (7, 2, -1)"

EXAMPLE - ERROR CASES:
Input: current=(unknown), target=(10, -5, 3)
Output: {"error": "Cannot calculate movement deltas - current position is unknown"}

Input: current=(0, 0, 0), target=(10, -5, 3), grid=(dimensions not specified)
Output: {"error": "Cannot plan grid scan - scan dimensions are not specified"}
</example>

<critical_reminders>
- Direction mapping: X negative=left/positive=right, Y negative=forward/positive=backward, Z negative=down/positive=up
- Grid scan NxM moves from (X, Y, Z) to (X+N, Y+M, Z)
- After grid scan, return movements must bring position back to home position (0, 0, 0)
- Think through each calculation step before generating output
- If you cannot calculate movements or positions confidently, return an error JSON instead of guessing
- Say "I don't know" via the error schema rather than making uncertain calculations
</critical_reminders>

{{ ctx.output_format }}
Use the error schema if:
- You cannot confidently calculate positions or movements
- Parameters are missing, contradictory, or unsafe
- Any step in the plan cannot be determined with certainty
"#
}

// Test Cases
// Test Case 1: Basic movement from origin
test TestBasicMovementFromOrigin {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-001"
      grid {
        rows 5
        cols 5
      }
      signal [
        {
          key "frequency"
          value "1000"
        },
        {
          key "amplitude"
          value "5.0"
        },
        {
          key "waveform"
          value "sine"
        }
      ]
      relative_offset_mm {
        x 10
        y -20
        z 15
      }
      filename "exp001.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 1
      }
      home_position {
        x 0
        y 0
        z 1
      }
    }
  }
}

// Test Case 2: Movement with negative offsets
test TestNegativeOffsets {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-002"
      grid {
        rows 3
        cols 4
      }
      signal [
        {
          key "frequency"
          value "2000"
        },
        {
          key "amplitude"
          value "3.5"
        }
      ]
      relative_offset_mm {
        x -15
        y -10
        z -5
      }
      filename "exp002.dat"
    }
    state {
      current_position {
        x 5
        y 10
        z 8
      }
      home_position {
        x 5
        y 10
        z 8
      }
    }
  }
}

// Test Case 3: No Z-axis movement (delta Z = 0)
test TestNoZMovement {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-003"
      grid {
        rows 2
        cols 2
      }
      signal [
        {
          key "frequency"
          value "1500"
        },
        {
          key "amplitude"
          value "4.0"
        },
        {
          key "offset"
          value "1.5"
        }
      ]
      relative_offset_mm {
        x 8
        y 12
        z 0
      }
      filename "exp003.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 5
      }
      home_position {
        x 0
        y 0
        z 5
      }
    }
  }
}

// Test Case 4: Only Z-axis movement
test TestOnlyZMovement {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-004"
      grid {
        rows 1
        cols 1
      }
      signal [
        {
          key "frequency"
          value "500"
        }
      ]
      relative_offset_mm {
        x 0
        y 0
        z 10
      }
      filename "exp004.dat"
    }
    state {
      current_position {
        x 20
        y 30
        z -5
      }
      home_position {
        x 20
        y 30
        z -5
      }
    }
  }
}

// Test Case 5: Large grid scan
test TestLargeGridScan {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-005"
      grid {
        rows 10
        cols 10
      }
      signal [
        {
          key "frequency"
          value "3000"
        },
        {
          key "amplitude"
          value "7.5"
        },
        {
          key "waveform"
          value "square"
        }
      ]
      relative_offset_mm {
        x 50
        y 50
        z 25
      }
      filename "exp005.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 6: Non-zero starting position different from home
test TestNonZeroStartDifferentFromHome {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-006"
      grid {
        rows 3
        cols 3
      }
      signal [
        {
          key "frequency"
          value "1200"
        },
        {
          key "amplitude"
          value "6.0"
        },
        {
          key "offset"
          value "2.5"
        }
      ]
      relative_offset_mm {
        x 5
        y -5
        z 6
      }
      filename "exp006.dat"
    }
    state {
      current_position {
        x 5
        y 10
        z -3
      }
      home_position {
        x 7
        y 2
        z -1
      }
    }
  }
}

// Test Case 7: Minimal grid scan (1x1)
test TestMinimalGridScan {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-007"
      grid {
        rows 1
        cols 1
      }
      signal [
        {
          key "frequency"
          value "800"
        },
        {
          key "amplitude"
          value "2.0"
        }
      ]
      relative_offset_mm {
        x 5
        y 5
        z 5
      }
      filename "exp007.dat"
    }
    state {
      current_position {
        x 10
        y 10
        z 10
      }
      home_position {
        x 10
        y 10
        z 10
      }
    }
  }
}

// Test Case 8: Mixed positive and negative movements
test TestMixedDirections {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-008"
      grid {
        rows 4
        cols 6
      }
      signal [
        {
          key "frequency"
          value "2500"
        },
        {
          key "amplitude"
          value "8.0"
        },
        {
          key "offset"
          value "-1.0"
        },
        {
          key "waveform"
          value "triangle"
        }
      ]
      relative_offset_mm {
        x -20
        y 15
        z -10
      }
      filename "exp008.dat"
    }
    state {
      current_position {
        x 30
        y -5
        z 20
      }
      home_position {
        x 30
        y -5
        z 20
      }
    }
  }
}

// Test Case 9: Return to home requires all three axes
test TestComplexReturnPath {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-009"
      grid {
        rows 5
        cols 7
      }
      signal [
        {
          key "frequency"
          value "1800"
        },
        {
          key "amplitude"
          value "5.5"
        }
      ]
      relative_offset_mm {
        x 25
        y -30
        z 12
      }
      filename "exp009.dat"
    }
    state {
      current_position {
        x -10
        y 15
        z -8
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 10: Multiple signal parameters
test TestMultipleSignalParameters {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-010"
      grid {
        rows 6
        cols 6
      }
      signal [
        {
          key "frequency"
          value "5000"
        },
        {
          key "amplitude"
          value "10.0"
        },
        {
          key "offset"
          value "3.0"
        },
        {
          key "waveform"
          value "sawtooth"
        },
        {
          key "duty_cycle"
          value "50"
        },
        {
          key "phase"
          value "90"
        }
      ]
      relative_offset_mm {
        x 15
        y 15
        z 15
      }
      filename "exp010.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 11: Small movements with decimal precision implications
test TestSmallMovements {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-011"
      grid {
        rows 1
        cols 1
      }
      signal [
        {
          key "frequency"
          value "100"
        },
        {
          key "amplitude"
          value "0.5"
        }
      ]
      relative_offset_mm {
        x 1
        y 2
        z 3
      }
      filename "exp011.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 12: Already at target position (all deltas = 0)
test TestAlreadyAtTarget {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-012"
      grid {
        rows 2
        cols 2
      }
      signal [
        {
          key "frequency"
          value "1000"
        },
        {
          key "amplitude"
          value "5.0"
        }
      ]
      relative_offset_mm {
        x 0
        y 0
        z 0
      }
      filename "exp012.dat"
    }
    state {
      current_position {
        x 10
        y 10
        z 10
      }
      home_position {
        x 10
        y 10
        z 10
      }
    }
  }
}

// Test Case 13: Asymmetric grid
test TestAsymmetricGrid {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-013"
      grid {
        rows 2
        cols 8
      }
      signal [
        {
          key "frequency"
          value "2200"
        },
        {
          key "amplitude"
          value "4.5"
        }
      ]
      relative_offset_mm {
        x 20
        y -15
        z 8
      }
      filename "exp013.dat"
    }
    state {
      current_position {
        x 5
        y 5
        z 5
      }
      home_position {
        x 5
        y 5
        z 5
      }
    }
  }
}

// Test Case 14: Home position at negative coordinates
test TestNegativeHomePosition {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-014"
      grid {
        rows 3
        cols 3
      }
      signal [
        {
          key "frequency"
          value "1500"
        },
        {
          key "amplitude"
          value "6.5"
        }
      ]
      relative_offset_mm {
        x 10
        y 10
        z 10
      }
      filename "exp014.dat"
    }
    state {
      current_position {
        x -20
        y -20
        z -20
      }
      home_position {
        x -20
        y -20
        z -20
      }
    }
  }
}

// Test Case 15: Single signal parameter
test TestSingleSignalParameter {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-015"
      grid {
        rows 4
        cols 4
      }
      signal [
        {
          key "frequency"
          value "750"
        }
      ]
      relative_offset_mm {
        x 12
        y 8
        z 4
      }
      filename "exp015.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// ====================================================== ERROR HANDLING TEST CASES ===============================================
// Test Case 2: Missing current position data
test TestMissingCurrentPosition {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-002"
      grid {
        rows 3
        cols 3
      }
      signal [
        {
          key "frequency"
          value "1200"
        }
      ]
      relative_offset_mm {
        x 5
        y 5
        z 5
      }
      filename "exp002.dat"
    }
    state {
      current_position {
        x null  // Missing/unknown position
        y null
        z null
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 3: Missing grid dimensions
test TestMissingGridDimensions {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-003"
      grid {
        rows null  // Grid dimensions not specified
        cols null
      }
      signal [
        {
          key "frequency"
          value "1500"
        }
      ]
      relative_offset_mm {
        x 10
        y 10
        z 10
      }
      filename "exp003.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 4: Missing home position
test TestMissingHomePosition {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-004"
      grid {
        rows 4
        cols 4
      }
      signal [
        {
          key "frequency"
          value "2000"
        }
      ]
      relative_offset_mm {
        x 15
        y -10
        z 5
      }
      filename "exp004.dat"
    }
    state {
      current_position {
        x 5
        y 5
        z 5
      }
      home_position {
        x null  // Missing home position
        y null
        z null
      }
    }
  }
}

// Test Case 5: Missing target position
test TestMissingTargetPosition {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-005"
      grid {
        rows 2
        cols 2
      }
      signal [
        {
          key "frequency"
          value "1800"
        }
      ]
      relative_offset_mm {
        x null  // Missing target offset
        y null
        z null
      }
      filename "exp005.dat"
    }
    state {
      current_position {
        x 10
        y 10
        z 10
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 6: Contradictory positions (target equals current but grid scan needed)
test TestContradictoryPositions {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-006"
      grid {
        rows 5
        cols 5
      }
      signal [
        {
          key "frequency"
          value "1000"
        }
      ]
      relative_offset_mm {
        x 0  // Target same as current
        y 0
        z 0
      }
      filename "exp006.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 10  // Home different from current/target - contradictory
        y 10
        z 10
      }
    }
  }
}

// Test Case 7: Missing signal parameters
test TestMissingSignalParameters {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-007"
      grid {
        rows 3
        cols 3
      }
      signal []  // Empty signal parameters
      relative_offset_mm {
        x 5
        y 5
        z 5
      }
      filename "exp007.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 8: Invalid/negative grid dimensions
test TestInvalidGridDimensions {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-008"
      grid {
        rows -3  // Invalid negative dimension
        cols 0   // Invalid zero dimension
      }
      signal [
        {
          key "frequency"
          value "1200"
        }
      ]
      relative_offset_mm {
        x 10
        y 10
        z 10
      }
      filename "exp008.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 9: Extreme position values (potential safety issue)
test TestUnsafeExtremePositions {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-009"
      grid {
        rows 2
        cols 2
      }
      signal [
        {
          key "frequency"
          value "1000"
        }
      ]
      relative_offset_mm {
        x 10000  // Extremely large movement - potentially unsafe
        y 10000
        z 10000
      }
      filename "exp009.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 10: Partial missing data (only one coordinate missing)
test TestPartialMissingCoordinate {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-010"
      grid {
        rows 4
        cols 4
      }
      signal [
        {
          key "frequency"
          value "1500"
        }
      ]
      relative_offset_mm {
        x 10
        y null  // Only Y coordinate missing
        z 5
      }
      filename "exp010.dat"
    }
    state {
      current_position {
        x 5
        y 5
        z 5
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 11: Empty experiment ID
test TestMissingExperimentID {
  functions [ExpPlanner]
  args {
    experiment {
      id ""  // Empty experiment ID
      grid {
        rows 3
        cols 3
      }
      signal [
        {
          key "frequency"
          value "1000"
        }
      ]
      relative_offset_mm {
        x 10
        y 10
        z 10
      }
      filename "exp011.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 12: Scan end position would exceed safe bounds
test TestScanExceedsBounds {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-012"
      grid {
        rows 1000  // Huge grid that could exceed bounds
        cols 1000
      }
      signal [
        {
          key "frequency"
          value "1200"
        }
      ]
      relative_offset_mm {
        x 500
        y 500
        z 50
      }
      filename "exp012.dat"
    }
    state {
      current_position {
        x 0
        y 0
        z 0
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}