Got it — let’s **stop abstract talk** and walk through **one concrete, end-to-end example** using *your exact sentence*, showing **what each agent outputs** and **where the “go back / move left / repeat” logic actually lives**.

I’ll keep this **mechanical and explicit**, not conceptual.

---

# User Command (Input)

> **“Scan for me 20x20 with gaussian using 1000Hz, move to left 30mm and do the same with 2000Hz. and so on, number of scan is 5”**

---

# 🔹 Step 1 — Router (Intent Only)

**Input:** raw user text
**Output:**

```json
{
  "intent": "multi_experiment_scan"
}
```

Router is done. Nothing smart here.

---

# 🔹 Step 2 — Orchestrator (EXPERIMENT COMPILER)

This is the MOST important step.

👉 The orchestrator **does NOT generate movement steps**
👉 It only **expands user intent into structured experiments**

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
  "global_constraints": {
    "return_home_after_each_experiment": true
  }
}
```

⚠️ Notice:

* **NO `move_x`, `scan()`, `home()`**
* Just *what* each experiment is
* Offset is **relative**, not absolute

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
}
```

### Planner Output (ABSTRACT PLAN)

```text
PLAN exp_2:
  1. move_to_offset(-30, 0)
  2. configure_signal(gaussian, 2000Hz)
  3. execute_grid_scan(20x20)
  4. return_home
```

🔑 Still **no loops**, **no motor commands**

---

# 🔹 Step 5 — Executor (RULES LIVE HERE)

Now your **existing rule-based logic finally has a correct home**.

### Example executor logic (simplified)

```python
def move_to_offset(dx, dy):
    home = state.home
    target = {
        "x": home["x"] + dx,
        "y": home["y"] + dy
    }
    safe_move_to(target)

def execute_grid_scan(rows, cols):
    start = state.current_position
    for i in range(rows):
        for j in range(cols):
            scan()
            move_x(step_x)
        move_y(step_y)
        move_x(-cols * step_x)
```

This is:

* Deterministic
* Testable
* Replaceable for another NDT system

---

# 🔹 Step 6 — Full Execution (WHAT ACTUALLY HAPPENS)

### For `exp_2` (2000Hz):

```
home (0,0)
→ move to (-30,0)
→ configure gaussian @2000Hz
→ scan 20x20
→ return home
```

Then:

```
home (0,0)
→ move to (-60,0)
→ configure gaussian @3000Hz
→ scan 20x20
→ return home
...
```

Exactly what the user asked.

---

# 🔥 Why This Finally Click Should Click

### Where is “move left 30mm”?

👉 **Orchestrator → relative_offset**

### Where is “do the same 5 times”?

👉 **Orchestrator → experiment_series**

### Where is “go back home”?

👉 **Global constraint**

### Where is your rule-set?

👉 **Executor ONLY**

---

# 🧠 One Sentence Summary (IMPORTANT)

> **LLM decides *what experiments exist*.
> Code decides *how motion and scanning happen*.**


