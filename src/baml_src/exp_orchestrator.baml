class ExperimentWithFilename {
  experiment map<string, string> @description("single experiment with key-value pairs")
  filename string @description("filename for this specific experiment without extension")
}

class ExpOrchestratorOutput {
  number_of_scans int @description("total number of scans to be performed")
  experiments ExperimentWithFilename[] @description("list of experiments with filenames")
  response string @description("natural language response summarizing the experiments")
}

function ExpOrchestrator(
  user_message: string, 
  conversation_history: ConversationMessage[]?)
-> ExpOrchestratorOutput {
  client GroqRouter
  prompt #"
You are a lab automation agent that converts natural language into structured JSON experiments with individual filenames.

EXPERIMENT PARSING RULES:
1. Split on: commas, "and", "then", "next", "after"
2. Parameters persist unless changed
3. Infer parameter keys: "20x20"→scan_dimensions, "gaussian"→scan_type, "1kHz"→frequency, etc.
4. Use snake_case; omit null values
5. EXPAND RANGES: "10 to 30"→[10,20,30], "1000 to 1200Hz"→[1000,1050,1100,1150,1200]
6. CREATE CARTESIAN PRODUCT: When multiple parameters have ranges, create separate experiments for ALL combinations
   - Example: 3 areas × 5 frequencies = 15 experiments
7. Each experiment object must have SINGLE values, not arrays

FILENAME GENERATION RULES (Applied to EACH experiment):
- Format: {pulse_mode}_{key_parameters_with_values}
- Use underscores to separate components
- Include ONLY the specific parameter values for THIS experiment
- Prioritize the most distinctive experimental parameters
- Keep total length under 50 characters
- Use standard abbreviations (amp=amplitude, freq=frequency, atten=attenuation, etc.)
- For scan dimensions, use format: {xl}x{yl} (e.g., 20x20)
- DON'T include "scan" in filename
- Each filename must be UNIQUE and reflect the specific parameter combination

EXAMPLES:

Input: "scan 10x10 and 20x20 gaussian at 1kHz and 2kHz"
Output:
{
  "number_of_scans": 4,
  "experiments": [
    {
      "experiment": {"scan_dimensions": "10x10", "scan_type": "gaussian", "frequency": "1000Hz"},
      "filename": "gaussian_10x10_freq1000"
    },
    {
      "experiment": {"scan_dimensions": "10x10", "scan_type": "gaussian", "frequency": "2000Hz"},
      "filename": "gaussian_10x10_freq2000"
    },
    {
      "experiment": {"scan_dimensions": "20x20", "scan_type": "gaussian", "frequency": "1000Hz"},
      "filename": "gaussian_20x20_freq1000"
    },
    {
      "experiment": {"scan_dimensions": "20x20", "scan_type": "gaussian", "frequency": "2000Hz"},
      "filename": "gaussian_20x20_freq2000"
    }
  ],
  "response": "Created 4 gaussian scan experiments with dimensions 10x10 and 20x20 at frequencies 1kHz and 2kHz."
}

Input: "gaussian 50x50 at 5kHz amplitude 2.1V"
Output:
{
  "number_of_scans": 1,
  "experiments": [
    {
      "experiment": {"scan_type": "gaussian", "scan_dimensions": "50x50", "frequency": "5000Hz", "amplitude": "2.1V"},
      "filename": "gaussian_50x50_freq5000_amp2.1V"
    }
  ],
  "response": "Created 1 gaussian scan experiment at 50x50, 5kHz, 2.1V amplitude."
}

{% if conversation_history %}
Recent conversation context:
<conversation_history>
{% for message in conversation_history %}
{{ message.role }}: {{ message.content }}
{% endfor %}
</conversation_history>
{% endif %}

<user_message>
{{ user_message }}
</user_message>

{{ ctx.output_format }}
"#
}

test TestOrchestrator {
  functions [ExpOrchestrator]
  args {
    user_message #"
# EXPERIMENTAL PLAN: VAE Data Collection for Early Corrosion Detection

## GOAL
Acquire a comprehensive dataset of Pulsed Eddy Current (PEC) signals from both pristine and early-stage corroded Al2024 samples to train and validate a Variational Autoencoder (VAE) for anomaly detection.

## SAMPLES
- **Pristine Al2024:** 10 samples (100mm x 100mm x 5mm, typical aerospace alloy thickness). These will serve as the "healthy" baseline.
- **Early-Stage Corroded Al2024:** 20 samples (100mm x 100mm x 5mm). These samples will have artificially introduced, controlled corrosion defects of varying severities and depths (e.g., 5%, 10%, 15% material loss localized to distinct areas, depth 0.1mm - 0.5mm) to represent early-stage degradation. Corroded areas should be well-characterized prior to PEC scanning using gravimetric analysis or profilometry.

## SCAN APPROACH
- **Constant Parameters:** All scans will use a Gaussian waveform with `Gauss amp = 2.1V`, `Gauss freq = 1000 Hz`, `Gauss Nor.Band = 0.5`, `Gauss atten = 6 dB`. Lift-off will be fixed at 1.0 mm for all scans.
- **Varying Parameters:** To introduce controlled variability representative of real-world scenarios, a subset of healthy and corroded samples will be scanned with slight variations in:
    - **StepX/StepY:** 1mm, 2mm (to assess resolution impact)
    - **Speed:** 1 mm/s, 2 mm/s (to assess scan speed impact on signal quality/noise)
    - **Probe Orientation:** Introduce 0, 90, 180, 270 degree rotations for 2 healthy and 4 corroded samples to simulate deployment variability. This simulates real-world usage conditions where precise probe alignment might not always be achievable.

## PROCEDURE
1.  **Baseline Healthy Data Collection:**
    *   Place a pristine Al2024 sample on the scanning platform.
    *   Set `Lift-off` to 1.0 mm.
    *   Execute a full 100mm x 100mm scan at `StepX = 1mm`, `StepY = 1mm`, `Speed = 2 mm/s`.
    *   Repeat for all 10 pristine samples, varying `StepX/StepY` and `Speed` as specified in "Varying Parameters" for designated samples.
    *   For the 2 designated samples, re-scan with probe rotations (0, 90, 180, 270 degrees).
2.  **Early-Stage Corroded Data Collection:**
    *   Place a corroded Al2024 sample on the scanning platform, ensuring known corroded areas are within the scan region.
    *   Set `Lift-off` to 1.0 mm.
    *   Execute a full 100mm x 100mm scan at `StepX = 1mm`, `StepY = 1mm`, `Speed = 2 mm/s`.
    *   Repeat for all 20 corroded samples, varying `StepX/StepY` and `Speed` as specified in "Varying Parameters" for designated samples.
    *   For the 4 designated samples, re-scan with probe rotations (0, 90, 180, 270 degrees).
3.  **Data Labeling and Annotation:**
    *   For each corroded sample scan, precisely label the spatial coordinates (X, Y) corresponding to the known corroded areas, along with their estimated severity (e.g., % material loss) and depth. This ground truth is crucial for training and validation.

## WATCH FOR
-   **Lift-off consistency:** Manual lift-off verification before each scan, especially for different samples, to ensure the 1.0mm setting is maintained.
-   **Sensor Drift/Noise:** Periodically scan a reference pristine sample (e.g., every 5 samples) to monitor for sensor drift or increased noise floor. Re-run scans if significant deviation from initial reference is observed.
-   **Sample Placement:** Ensure consistent sample orientation and placement to enable accurate defect mapping.
-   **Robotic Arm Stability:** Monitor for any vibrations or jerky movements that could introduce noise into the signal.

## SUCCESS CHECK
-   A minimum of 500 individual PEC time-domain signals (500 samples each) acquired per 100x100mm scan area (~10,000 data points per scan).
-   Consistent signal characteristics for healthy samples, with observable and distinct deviations in corroded areas.
-   Accurate spatial mapping of known corrosion defects within the acquired data for at least 80% of corroded samples.
-   Variation in scanning parameters (StepX/Y, Speed, Probe Orientation) introduces slight but manageable signal variance, allowing the VAE to learn robust feature representations.
    "#
  }
}

