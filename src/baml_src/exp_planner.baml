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
  1. move [axis] [direction] (distance [value] mm)
  ...
  N. configure signal (frequency=[value], amplitude=[value], offset=[value], etc.)
  N+1. execute grid scan ([N]x[M])
  N+2. move X [direction] (distance [value] mm)  # return to target X
  N+3. move Y [direction] (distance [value] mm)  # return to target Y

DETAILED INSTRUCTIONS:
1. Add signal configuration command with the exact parameters provided
2. Calculate movement deltas: target position minus current position
3. Generate movement commands in order: X axis first, then Y axis, then Z axis
4. Omit any movement step where delta equals 0
5. Add grid scan execution command
6. Calculate scan end position: After NxM grid scan starting at (X, Y, Z), final position is (X+N, Y+M, Z)
7. Generate return movement commands to reach target position from scan end position
8. Use movement order X, Y for return (omit Z if unchanged)
9. Think step-by-step before generating the plan
10. Only provide a plan if you are confident in all calculations
</instructions>

<example>
EXAMPLE - SUCCESS CASE:
Input: current=(0, 0, 0), target=(10, -5, 3), signal=(frequency=1200, amplitude=6.0, offset=2.5), grid=2x2

Output:
"PLAN EXP-XXX:
  1. move X right (distance 10 mm)
  2. move Y forward (distance 5 mm)
  3. move Z up (distance 3 mm)
  4. configure signal (frequency=1200, amplitude=6.0, offset=2.5)
  5. execute grid scan (2x2)
  6. move X left (distance 2 mm)  # return from (12, -3, 3) to (10, -3, 3)
  7. move Y forward (distance 2 mm)  # return from (10, -3, 3) to (10, -5, 3)"

EXAMPLE - ERROR CASES:
Input: current=(unknown), target=(10, -5, 3)
Output: {"error": "Cannot calculate movement deltas - current position is unknown"}

Input: current=(0, 0, 0), target=(10, -5, 3), grid=(dimensions not specified)
Output: {"error": "Cannot plan grid scan - scan dimensions are not specified"}
</example>

<critical_reminders>
- Direction mapping: X negative=left/positive=right, Y negative=forward/positive=backward, Z negative=down/positive=up
- Grid scan NxM moves from (X, Y, Z) to (X+N, Y+M, Z)
- For this experiment: 5x5 scan at (10, -20, 15) ends at (15, -15, 15)
- Return movements must bring position back to exact target (10, -20, 15)
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

// Test Case 2: Already at target position (no movement needed)
test TestNoMovementNeeded {
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
          value "500"
        },
        {
          key "amplitude"
          value "3.0"
        }
      ]
      relative_offset_mm {
        x 50
        y 30
        z 10
      }
      filename "exp002.dat"
    }
    state {
      current_position {
        x 50
        y 30
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

// Test Case 3: Movement with negative deltas (left, forward, down)
test TestNegativeMovement {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-003"
      grid {
        rows 10
        cols 8
      }
      signal [
        {
          key "frequency"
          value "2000"
        },
        {
          key "amplitude"
          value "7.5"
        },
        {
          key "phase"
          value "90"
        },
        {
          key "duration"
          value "100"
        }
      ]
      relative_offset_mm {
        x -25
        y -40
        z -15
      }
      filename "exp003.dat"
    }
    state {
      current_position {
        x 10
        y 20
        z 30
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 4: Complex movement from non-origin home position
test TestNonOriginHome {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-004"
      grid {
        rows 7
        cols 12
      }
      signal [
        {
          key "frequency"
          value "1500"
        },
        {
          key "amplitude"
          value "4.2"
        },
        {
          key "waveform"
          value "square"
        }
      ]
      relative_offset_mm {
        x 30
        y 15
        z -20
      }
      filename "exp004.dat"
    }
    state {
      current_position {
        x 5
        y -10
        z 25
      }
      home_position {
        x 100
        y 50
        z 75
      }
    }
  }
}

// Test Case 5: Large grid scan with single axis movement
test TestSingleAxisMovement {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-005"
      grid {
        rows 20
        cols 20
      }
      signal [
        {
          key "frequency"
          value "800"
        }
      ]
      relative_offset_mm {
        x 0
        y 0
        z 50
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

// Test Case 6: All positive movements (right, backward, up)
test TestAllPositiveMovements {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-006"
      grid {
        rows 4
        cols 6
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
        x 45
        y 60
        z 35
      }
      filename "exp006.dat"
    }
    state {
      current_position {
        x -10
        y -20
        z -15
      }
      home_position {
        x 0
        y 0
        z 0
      }
    }
  }
}

// Test Case 7: Minimal signal parameters
test TestMinimalSignal {
  functions [ExpPlanner]
  args {
    experiment {
      id "EXP-007"
      grid {
        rows 2
        cols 2
      }
      signal [
        {
          key "enabled"
          value "true"
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