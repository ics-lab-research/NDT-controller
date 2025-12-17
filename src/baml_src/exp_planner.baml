function ExpPlanner(experiment: Experiment, state: State) -> string {
  client GroqRouter
  prompt #"
You are an experiment planning system for experiment "{{ experiment.id }}".

COORDINATE SYSTEM:
- X-axis: negative = left, positive = right
- Y-axis: negative = forward, positive = backward  
- Z-axis: negative = down, positive = up

CURRENT SITUATION:
- Current position: ({{ state.current_position.x }}, {{ state.current_position.y }}, {{ state.current_position.z }}) mm
- Home position: ({{ state.home_position.x }}, {{ state.home_position.y }}, {{ state.home_position.z }}) mm
- Target offset from home: ({{ experiment.relative_offset_mm.x }}, {{ experiment.relative_offset_mm.y }}, {{ experiment.relative_offset_mm.z }}) mm

TASK:
Generate a movement plan to:
1. Move from current position to the target position (home + relative offset);
2. Configure signal with parameters: {% for param in experiment.signal %}{{ param.key }}={{ param.value }}{% if not loop.last %}, {% endif %}{% endfor %};
3. Execute {{ experiment.grid.rows }}x{{ experiment.grid.cols }} grid scan;
4. Return to home position

OUTPUT FORMAT (use exact axis names and calculate deltas):
PLAN {{ experiment.id }}:
  1. move Y [forward/backward] (distance [calculated_value] mm)
  2. move X [left/right] (distance [calculated_value] mm)
  3. move Z [up/down] (distance [calculated_value] mm)
  4. configure signal({% for param in experiment.signal %}{{ param.key }}={{ param.value }}{% if not loop.last %}, {% endif %}{% endfor %})
  5. execute grid scan({{ experiment.grid.rows }}x{{ experiment.grid.cols }})
  6. return home position

CALCULATION RULES:
- Target absolute position = home_position + relative_offset_mm
- Movement delta = target_position - current_position
- Only include movement steps where |delta| > 0
- Negative Y delta = forward, positive = backward
- Negative X delta = left, positive = right
- Negative Z delta = down, positive = upward
- Order movements: Y, X, Z

Generate the plan:
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