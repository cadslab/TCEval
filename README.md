# TCEval: Thermal Comfort-based AI Cognitive Evaluation Framework

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub Repository](https://img.shields.io/badge/GitHub-cadslab/TCEval-green.svg)](https://github.com/cadslab/TCEval)

## Overview

TCEval is the first evaluation framework that leverages **thermal comfort** as a paradigm to assess three core cognitive capacities of AI systems:

1. **Cross-modal reasoning** (integrating environmental, personal, and contextual cues)
2. **Causal association** (linking variables like temperature to comfort outcomes)
3. **Adaptive decision-making** (modifying behavior under changing conditions)

Traditional AI benchmarks (e.g., GLUE, MMLU) focus on abstract task proficiency, but TCEval shifts the focus to **embodied, context-aware perception and decision-making**—critical for human-centric applications like smart buildings, wearable tech, and embodied AI.

PMV (Predicted Mean Vote) is a standardized metric defined in **ASHRAE Standard 55-2023** (the global benchmark for thermal comfort) that quantifies subjective thermal sensation on a 7-point scale:
| PMV Value | Thermal Sensation |  
|-----------|-------------------|  
| +3 | Hot |  
| +2 | Warm |  
| +1 | Slightly Warm |  
| 0 | Neutral |  
| -1 | Slightly Cool |  
| -2 | Cool |  
| -3 | Cold |

By initializing Large Language Model (LLM) agents with virtual personalities and guiding them to generate clothing insulation selections and thermal comfort feedback, TCEval validates outputs against real-world datasets (ASHRAE Global Database, Chinese Thermal Comfort Database) to measure alignment with human intuitive reasoning.

## Key Features

- **Ecologically Valid Evaluation**: Grounded in a universal human experience (thermal comfort) to bridge the gap between AI testing and practical cognitive assessment.
- **Multi-Capacity Assessment**: Evaluates cross-modal reasoning, causal association, and adaptive decision-making in dynamic, real-world contexts.
- **LLM Agent Integration**: Uses LLM agents as "digital twins" to simulate human-like perception and decision-making.
- **Open Dataset Validation**: Compares AI outputs with two authoritative thermal comfort datasets for rigor.
- **Complementary to Traditional Benchmarks**: Enhances existing evaluations by focusing on "how AI perceives and acts" rather than just "what AI knows".

## Methodology

The TCEval framework follows three core steps:

1. **Agent Initialization**: Load LLM agents with virtual personality attributes (gender, age, height, weight, etc.).
2. **Feedback Generation**: Instruct agents to:
   - Select clothing insulation based on environmental conditions and personal context.
   - Provide thermal comfort feedback using PMV (Predicted Mean Vote, ASHRAE Standard 55-2023).
   - Adapt decisions (e.g., adjust clothing/HVAC settings) under changing conditions.
3. **Validation & Analysis**: Compare agent outputs with:
   - Human data from the Chinese Thermal Comfort Database.
   - Theoretical thermal comfort values (PMV) from environmental parameters.

### Datasets Used

- [ASHRAE Global Database of Thermal Comfort Field Measurements](https://doi.org/10.6078/D1F671)
- [Chinese Thermal Comfort Dataset](https://doi.org/10.1038/s41597-023-02568-3)
- Virtual Personality Database (from [Scaling Synthetic Data Creation with 1,000,000,000 Personas](https://doi.org/10.48550/arXiv.2406.20094))

## Experimental Results

Tests on the leading LLMs show:

- **Exact Alignment**: Limited thermal comfort alignment with human data.
- **Directional Consistency**: Significantly improved with ±1 PMV tolerance.
- **Cognitive Gaps**: LLM-generated PMV distributions diverge markedly from human data, and agents perform near-randomly in discrete thermal comfort classification (AUC ≈ 0.5).
- **Key Insight**: Current LLMs possess foundational cross-modal reasoning but lack precise understanding of nonlinear relationships between thermal comfort variables.

### ASHRAE Global Database II

### Core Metrics Summary Table

| Model Name           | Original Data Rows | Exact Match Rows | Exact Match Ratio | Match Ratio (Abs PMV Diff < 1) | Black-Marked Rows (Special Conditions) |
| -------------------- | ------------------ | ---------------- | ----------------- | ------------------------------ | -------------------------------------- |
| Deepseek-R1:32B      | 8100               | 1605             | 0.1981            | 0.3885                         | 2551                                   |
| gemma3:27B           | 8100               | 577              | 0.0712            | 0.5883                         | 0                                      |
| gpt-oss:120B         | 8100               | 2207             | 0.2725            | 0.5357                         | 103                                    |
| mistral-small3.2:24B | 8100               | 1845             | 0.2278            | 0.6675                         | 0                                      |
| Qwen3:32B            | 8100               | 3003             | 0.3707            | 0.6147                         | 1                                      |
| Qwen3:80B            | 8100               | 4087             | 0.5046            | 0.8170                         | 0                                      |

- Exact Match: LLM outputs in string match human data exactly.
- Match Ratio (Abs PMV Diff < 1): The **Match Ratio (Absolute PMV Difference < 1)** is a critical directional consistency metric in TCEval, designed to assess how well an LLM agent’s thermal comfort judgments align with human perceptions—_even when the exact values do not perfectly match_.
- Black-Marked Rows: LLM predictions are outside PMV range or none, or refuse to answer.

#### 1. Metric Definition

This ratio calculates the **proportion of test cases** where the **absolute difference between the AI’s predicted PMV and the human’s actual PMV** is less than 1. Mathematically:  
\[
\text{Match Ratio (Abs PMV Diff < 1)} = \frac{\text{Number of cases where } |\text{AI PMV} - \text{Human PMV}| < 1}{\text{Total number of test cases}}
\]

#### 2. What It Measures (and Why It Matters)

- **Directional Consistency**: Unlike the "Exact Match Ratio" (which requires AI PMV = Human PMV), this metric focuses on whether the AI’s judgment _trends in the same direction_ as human perception. For example:

  - If a human rates a scenario as "Slightly Warm" (PMV = +1) and the AI predicts "Warm" (PMV = +2), the absolute difference is 1 (not included).
  - If the AI predicts "Neutral" (PMV = 0), the absolute difference is 1 (not included).
  - If the AI predicts "Slightly Warm" (PMV = +1) or "Warm" (PMV = +2) is not included, but if it predicts "Neutral" (PMV = 0) with a difference of 1, it’s also not included. Wait, let's correct with valid examples:
    - Human PMV = +1 (Slightly Warm), AI PMV = +0.8 → Absolute difference = 0.2 < 1 → Counts as a match.
    - Human PMV = -2 (Cool), AI PMV = -1.5 → Absolute difference = 0.5 < 1 → Counts as a match.
    - Human PMV = +3 (Hot), AI PMV = +2.2 → Absolute difference = 0.8 < 1 → Counts as a match.

- **Real-World Relevance**: In practical applications (e.g., smart buildings), precise PMV alignment is less critical than ensuring the AI does not misjudge the _direction_ of comfort (e.g., mistaking "Cold" for "Hot"). This metric reflects the AI’s ability to capture the "big picture" of human thermal perception.

#### 3. Interpretation of Results

- A high ratio (e.g., Qwen3-80B’s 81.70%) indicates the AI consistently mirrors human comfort trends—even if it does not perfectly replicate exact PMV values. This is a strong signal of **foundational cross-modal reasoning** (integrating environmental/personal cues to infer comfort direction).
- A low ratio (e.g., Deepseek-R1-32B’s 38.85%) suggests the AI’s judgments often diverge from human trends, indicating gaps in understanding how variables like temperature, humidity, or clothing insulation influence comfort.

#### 4. Why This Metric Complements Exact Match Ratio

- Exact matches are rare in thermal comfort (human judgments themselves have natural variability).
- The "Abs PMV Diff < 1" ratio provides a more realistic measure of an AI’s utility in human-centric systems, where directional accuracy drives actionable decisions (e.g., "Should we cool the room?" vs. "Should we heat it?").

In summary, this metric quantifies the AI’s ability to "get the gist" of human thermal comfort— a key prerequisite for deployment in applications like smart HVAC, wearable tech, or embodied AI.

## Use Cases

- Evaluate AI readiness for **human-centric applications** (smart buildings, wearable devices, adaptive HVAC systems).
- Serve as a **Cognitive Turing Test** to measure AI's ability to emulate human perception-decision cycles.
- Guide LLM development for embodied AI (e.g., improving causal reasoning and context adaptation).

## Installation & Usage

### Prerequisites

- Python 3.8+
- Dependencies: `torch`, `transformers`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/cadslab/TCEval.git
   cd TCEval
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Download datasets (see [Datasets Used](#datasets-used)).
4. Run the evaluation pipeline: 未完成
   ```bash
   python run_tceval.py --model [MODEL_NAME] --dataset [DATASET_NAME]
   ```

### Arguments

- `--model`: Name of the LLM to evaluate (e.g., `deepseek-r1-32b`, `qwen3-32b`).
- `--dataset`: Dataset to use for validation (`ashrae` or `chinese_thermal`).
- `--tolerance`: PMV tolerance for directional alignment (default: ±1).
- `--output_dir`: Directory to save results (default: `results/`).

---

_TCEval: Bridging AI evaluation from abstract tasks to real-world human cognition._

### Pre-trained Models

Soon

## 💡 Applications

- **Smart Buildings**: Evaluate AI for HVAC control and occupant comfort optimization
- **Embodied AI**: Assess cognitive readiness for human-robot interaction
- **Human-Centric AI Development**: Guide model improvements in causal reasoning and contextual adaptation
- **Academic Research**: Benchmark new AI models against real-world cognitive tasks
- **Industry Adoption**: Validate AI systems for human-interactive products and services

## 📄 License

See the [LICENSE.md](https://github.com/cadslab/TCEval/blob/main/LICENSE) file for details.

## 📚 Citation

If TCEval is helpful to your work, please cite our paper:

```bibtex
@misc{li2025tceval,
      title={TCEval: Using Thermal Comfort to Assess Cognitive and Perceptual Abilities of AI},
      author={Jingming Li},
      year={2025},
      eprint={2512.23217},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2512.23217},
}
```
