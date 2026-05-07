# Cerebrasense

**Cerebrasense** is a high-performance, research-grade medical imaging platform designed for the classification of structural 3D MRI scans, with a primary focus on Alzheimer's disease detection using the OASIS-1 and OASIS-2 datasets.

Built on the **MONAI** (Medical Open Network for AI) framework and **PyTorch**, Cerebrasense provides a robust pipeline for data preprocessing, subject-safe splitting, and training state-of-the-art neural networks (like DenseNet121) to detect dementia with high precision.

---

## 🌟 Key Features

- **Advanced MONAI Integration**: Leverages dictionary-style transforms for deterministic preprocessing (Orientation, Spacing, Intensity Normalization).
- **Research-Grade Pipelines**: Supports Mixed Precision (AMP), Gradient Accumulation, Early Stopping, and Learning Rate Scheduling.
- **OASIS-2 Ready**: Specialized loaders for longitudinal OASIS-2 data, ensuring subject-safe splits (preventing data leakage across visits).
- **High-Performance Data Loading**: Utilizes `CacheDataset` for lightning-fast training by caching pre-processed volumes in memory.
- **Comprehensive Evaluation**: Automated generation of AUROC, Precision, Recall, F1-score, and Confusion Matrices.
- **Colab/Kaggle Optimized**: Includes dedicated notebooks and scripts for seamless training in cloud environments.

---

## 📁 Project Structure

```text
Cerebrasense/
├── alz_backend/           # Core implementation logic
│   ├── src/               # Source code (data loaders, models, transforms)
│   ├── configs/           # YAML configuration for training/transforms
│   ├── scripts/           # Core execution scripts
│   ├── requirements.txt   # Python dependencies
│   └── outputs/           # Training artifacts (checkpoints, metrics, reports)
├── scripts/               # Project-level wrapper scripts
├── notebooks/             # Colab and Kaggle training notebooks
├── OriginalDataset/       # (Ignored) Raw OASIS data
└── README.md              # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- NVIDIA GPU with CUDA support (recommended for training)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Billrichard209/cerebrasense.git
   cd cerebrasense/alz_backend
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🧠 Training the Model

### Supervised OASIS-2 Training (Research Grade)

To run a full research-grade training session with mixed precision and early stopping:

```bash
python scripts/train_oasis2.py --run-name my_experiment --epochs 50 --batch-size 2 --mixed-precision
```

### Fast MONAI Training (Smoke Test)

To verify the MONAI pipeline with a single epoch:

```bash
python scripts/train_oasis_monai.py --epochs 1 --batch-size 1
```

---

## 📈 Monitoring and Evaluation

After training, results are saved to `alz_backend/outputs/runs/`:

- **Checkpoints**: Best and last model weights (`.pt`).
- **Metrics**: Epoch-by-epoch loss and accuracy (`.csv` / `.json`).
- **Reports**: Markdown summaries including AUROC and Confusion Matrices.

---

## 🛠 Tech Stack

- **Framework**: [MONAI](https://monai.io/)
- **Core**: [PyTorch](https://pytorch.org/)
- **Data**: [Pandas](https://pandas.pydata.org/), [NiBabel](https://nipy.org/nibabel/)
- **Visuals**: [Matplotlib](https://matplotlib.org/), [Seaborn](https://seaborn.pydata.org/)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Acknowledgments

- The **OASIS** (Open Access Series of Imaging Studies) team for providing the datasets.
- The **MONAI** community for the incredible medical AI framework.