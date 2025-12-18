# User Command (Input)

> **“run 3 scans vertically separated by 15 millimeters, use sine wave 10x10 at 1000 hertz”**

---

# 🔹 Step 1 — Router (Intent Only)

**Input:** raw user text
**Output:**

```json
{
  "action": "MULTIPLE_SCAN",
  "response": null,
  "reformatted_message": "3 scans 15mm apart on Y axis: sine 10x10 at 1kHz"
}
```

Router is done. Nothing smart here.

---

# 🔹 Step 2 — Orchestrator (EXPERIMENT COMPILER)

### Orchestrator Input
```json
{
  "reformatted_message": "3 scans 15mm apart on Y axis: sine 10x10 at 1kHz"
}
```

### Orchestrator Output

```json
{
  "experiment_series": [
    {
      "id": "exp_1",
      "scan_type": "grid_scan",
      "grid": { "rows": 20, "cols": 20 },
      "signal": {
        "waveform": "gaussian",
        "frequency_hz": 1000
      },
      "relative_offset_mm": { "x": 0, "y": 0 }
    },
    {
      "id": "exp_2",
      "scan_type": "grid_scan",
      "grid": { "rows": 20, "cols": 20 },
      "signal": {
        "waveform": "gaussian",
        "frequency_hz": 2000
      },
      "relative_offset_mm": { "x": -30, "y": 0 }
    },
    {
      "id": "exp_3",
      "scan_type": "grid_scan",
      "grid": { "rows": 20, "cols": 20 },
      "signal": {
        "waveform": "gaussian",
        "frequency_hz": 3000
      },
      "relative_offset_mm": { "x": -60, "y": 0 }
    },
    {
      "id": "exp_4",
      "scan_type": "grid_scan",
      "grid": { "rows": 20, "cols": 20 },
      "signal": {
        "waveform": "gaussian",
        "frequency_hz": 4000
      },
      "relative_offset_mm": { "x": -90, "y": 0 }
    },
    {
      "id": "exp_5",
      "scan_type": "grid_scan",
      "grid": { "rows": 20, "cols": 20 },
      "signal": {
        "waveform": "gaussian",
        "frequency_hz": 5000
      },
      "relative_offset_mm": { "x": -120, "y": 0 }
    }
  ],

}
```

---

# 🔹 Step 3 — World State (THIS IS WHERE YOU WERE STUCK)

Initial state (tracked by system):

```json
{
  "home": { "x": 0, "y": 0, "z": 0 },
  "current_position": { "x": 0, "y": 0, "z": 0 },
  "status": "ready"
}
```

This agent **answers questions**, nothing else.

---

# 🔹 Step 4 — Planner (Hierarchical, Concrete)

Planner sees **ONE experiment at a time**.

### Planner Input (exp_2 example)

```json
{
"id": "exp_1",
"grid": {
    "rows": 10,
    "cols": 10
},
"signal": {
    "waveform": "gaussian",
    "frequency_hz": "1000"
},
"relative_offset_mm": {
    "x": 0,
    "y": 0,
    "z": 1
},
"filename": "gaussian_10x10_freq1000"
}
```

```json
{
  "home": { "x": 0, "y": 0, "z": 1 },
  "current_position": { "x": 20, "y": -30, "z": 5 },
  "scanning_status": "scanning"
}
```

### Planner Output (ABSTRACT PLAN)

```text
PLAN EXP-001:
1. configure signal (frequency=1000, amplitude=5.0, waveform=sine)
2. move X right (distance 10 mm)
3. move Y forward (distance 20 mm)
4. move Z up (distance 15 mm)
5. execute grid scan (5x5)
6. move X right (distance 5 mm)  # return from (5, -15, 15) to (10, -15, 15)\n  
7. move Y forward (distance 5 mm)  # return from (10, -15, 15) to (10, -20, 15)"
```

🔑 Still **no loops**, **no motor commands**

---

# 🔹 Step 5 — Executor (RULES LIVE HERE)

Now your **existing rule-based logic finally has a correct home**.

### Example executor logic (simplified)

```python
def move_to_offset(dx, dy):
  pass

def execute_grid_scan(rows, cols):
  pass
```

This is:

* Deterministic
* Testable
* Replaceable for another NDT system

---




