# TCEval: Thermal Comfort-based AI Cognitive Evaluation Framework

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub Repository](https://img.shields.io/badge/GitHub-cadslab/TCEval-green.svg)](https://github.com/cadslab/TCEval)

## Overview
TCEval is the first evaluation framework that leverages **thermal comfort** as a paradigm to assess three core cognitive capacities of AI systems:
1. **Cross-modal reasoning** (integrating environmental, personal, and contextual cues)
2. **Causal association** (linking variables like temperature to comfort outcomes)
3. **Adaptive decision-making** (modifying behavior under changing conditions)

Traditional AI benchmarks (e.g., GLUE, MMLU) focus on abstract task proficiency, but TCEval shifts the focus to **embodied, context-aware perception and decision-making**—critical for human-centric applications like smart buildings, wearable tech, and embodied AI.

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
Tests on four leading LLMs (Qwen3:32B, Mistral-Small3.2:24B, Gemma3:27B, Deepseek-R1:32B) show:
- **Exact Alignment**: Limited (best-performing model: DeepSeek-R1 with 31% exact match to human data).
- **Directional Consistency**: Significantly improved with ±1 PMV tolerance (DeepSeek-R1 reaches 57%, Qwen3:32B at 51%).
- **Cognitive Gaps**: LLM-generated PMV distributions diverge markedly from human data, and agents perform near-randomly in discrete thermal comfort classification (AUC ≈ 0.5).
- **Key Insight**: Current LLMs possess foundational cross-modal reasoning but lack precise understanding of nonlinear relationships between thermal comfort variables.

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
4. Run the evaluation pipeline:
   ```bash
   python run_tceval.py --model [MODEL_NAME] --dataset [DATASET_NAME]
   ```

### Arguments
- `--model`: Name of the LLM to evaluate (e.g., `deepseek-r1-32b`, `qwen3-32b`).
- `--dataset`: Dataset to use for validation (`ashrae` or `chinese_thermal`).
- `--tolerance`: PMV tolerance for directional alignment (default: ±1).
- `--output_dir`: Directory to save results (default: `results/`).


---

*TCEval: Bridging AI evaluation from abstract tasks to real-world human cognition.*

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
