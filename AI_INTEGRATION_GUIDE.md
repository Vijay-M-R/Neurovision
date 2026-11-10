# NeuroVision — AI Integration Guide

## 1. Project Overview

**Project:** NeuroVision — Medical Image Processing System for Brain MRI Enhancement and Multi-Region Tumor Segmentation.

**AI Engine:** MONAI SegResNet pretrained model.

**Framework:** Python, PyTorch, MONAI, NiBabel, OpenCV.

**Hardware:** NVIDIA GPU with CUDA support; CPU fallback available.

The AI engine performs:
- Four-modality MRI preprocessing.
- Brain tumor segmentation.
- Whole Tumor (WT), Tumor Core (TC), Enhancing Tumor (ET) extraction.
- Segmentation evaluation when ground truth is available.
- MRI contrast enhancement using CLAHE.
- Axial, coronal and sagittal visualization.
- Result generation and JSON storage.

## 2. Critical AI Development Rules

The following rules are mandatory:

1. Do not train a new model.
2. Do not fine-tune the existing model.
3. Do not modify pretrained model weights.
4. Do not replace MONAI SegResNet.
5. Do not create another neural network.
6. Do not change the existing model architecture.
7. Do not change model preprocessing or channel ordering.
8. Do not feed enhanced MRI into segmentation inference by default.
9. Do not claim that this system provides a clinical diagnosis.
10. Keep the AI engine independent from the frontend and backend.

Use the existing pretrained bundle:

`pretrained_models/brats_mri_segmentation/models/model.pt`

Bundle version: 0.5.2.

## 3. MRI Input Requirements

The current AI engine accepts one four-dimensional NIfTI file:

- `.nii`
- `.nii.gz`

Expected dimensions:

`(X, Y, Z, 4)`

Dataset modality order:

| Channel | Modality |
|---|---|
| 0 | FLAIR |
| 1 | T1 |
| 2 | T1ce |
| 3 | T2 |

The AI preprocessor automatically reorders channels to:

`[T1ce, T1, T2, FLAIR]`

Important:
- Do not assume the current engine accepts four separate modality files.
- Do not accept arbitrary 3D MRI files as valid segmentation input.
- Validate file format, dimensions, finite values and modality availability.
- Preserve the original MRI file.
- Preserve spatial affine and header information.

## 4. Existing AI Engine Structure

```text
ai_engine/
│
├── model/
│   └── loader.py
│
├── preprocessing/
│   └── mri_preprocessor.py
│
├── inference/
│   └── segmentation.py
│
├── enhancement/
│   └── enhancement.py
│
├── evaluation/
│   └── metrics.py
│
├── visualization/
│   └── mri_viewer.py
│
├── results/
│   └── result_manager.py
│
├── tests/
│
└── pipeline.py
```

Do not duplicate these modules in the backend.

The backend must import and call the existing AI functions.

## 5. AI Functions Available

### Model loading

```python
from ai_engine.model.loader import load_model, get_model_info

model, device = load_model()
info = get_model_info()
```

The model uses caching with `lru_cache(maxsize=1)`.

Load it once during backend startup and reuse it.

### MRI preprocessing

```python
from ai_engine.preprocessing.mri_preprocessor import prepare_mri

prepared = prepare_mri(mri_path, device)
```

Returns:
- Image tensor
- Affine
- NIfTI header
- Original dimensions
- Source path
- Model modality order

### Tumor segmentation

```python
from ai_engine.inference.segmentation import segment_mri

result = segment_mri(
    mri_path=mri_path,
    output_dir=output_dir
)
```

Returns:
- Patient ID
- Processing status
- Model information
- Processing time
- Combined prediction path
- Individual WT, TC and ET mask paths
- Tumor voxel counts
- Output dimensions

### Evaluation

```python
from ai_engine.evaluation.metrics import evaluate_segmentation

metrics = evaluate_segmentation(
    prediction_path,
    ground_truth_path
)
```

Metrics:
- Dice coefficient
- Intersection over Union
- Precision
- Recall
- TP, FP, FN and TN

Evaluation is optional. Never calculate evaluation metrics when ground truth is unavailable.

### MRI visualization

```python
from ai_engine.visualization.mri_viewer import create_mri_visualization

visualization = create_mri_visualization(
    mri_path,
    prediction_path,
    output_path,
    ground_truth_path=None
)
```

Generates original MRI, ground-truth and AI-prediction comparisons when ground truth is supplied.

### MRI enhancement

```python
from ai_engine.enhancement.enhancement import export_enhanced_mri_previews

enhancement = export_enhanced_mri_previews(
    mri_path,
    output_dir
)
```

Generates enhanced axial, coronal and sagittal PNG previews.

Enhancement is an independent visualization operation. It must not modify the segmentation input.

### Complete pipeline

```python
from ai_engine.pipeline import run_pipeline

result = run_pipeline(
    mri_path=mri_path,
    ground_truth_path=None,
    output_dir=output_dir,
    generate_visualization=True
)
```

This is the preferred backend integration entry point.

It performs segmentation, optional evaluation, visualization and JSON result generation.

## 6. Segmentation Output Labels

The combined prediction NIfTI uses:

| Label | Meaning |
|---|---|
| 0 | Background |
| 1 | Tumor Core |
| 2 | Whole Tumor outside Tumor Core |
| 4 | Enhancing Tumor |

Model output channels:

| Channel | Region |
|---|---|
| 0 | TC |
| 1 | WT |
| 2 | ET |

Individual masks are binary volumes.

Important:
- WT, TC and ET masks overlap.
- Do not add their voxel counts to calculate total tumor volume.
- Do not confuse the combined prediction labels with the original dataset labels.
- The current model output does not reliably separate necrotic tissue from non-enhancing tumor.

## 7. Recommended Backend Architecture

Use **Python FastAPI**.

Suggested backend structure:

```text
backend/
│
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── routes/
│   │   ├── health.py
│   │   ├── upload.py
│   │   ├── segmentation.py
│   │   ├── enhancement.py
│   │   └── results.py
│   │
│   ├── services/
│   │   ├── ai_service.py
│   │   ├── file_service.py
│   │   └── result_service.py
│   │
│   └── schemas/
│       ├── request.py
│       └── response.py
│
└── storage/
    ├── uploads/
    └── results/
```

The backend should call the AI engine through `ai_service.py`.

Do not copy model inference code into FastAPI routes.

## 8. Recommended API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Backend and AI health |
| GET | `/api/model-info` | Model information |
| POST | `/api/upload` | Upload MRI |
| POST | `/api/segment` | Run segmentation |
| POST | `/api/enhance` | Generate enhanced previews |
| GET | `/api/results/{id}` | Retrieve result JSON |
| GET | `/api/results/{id}/visualization` | View comparison PNG |
| GET | `/api/results/{id}/masks/{region}` | Retrieve individual mask |
| GET | `/api/results/{id}/download` | Download result files |

These are proposed endpoints, not existing endpoints. Implement them in the backend.

## 9. GPU and Inference Management

The development machine has an NVIDIA RTX 4050 Laptop GPU with 6 GB VRAM.

Rules:

1. Load the pretrained model once during FastAPI startup.
2. Reuse the cached model.
3. Avoid loading another model for each request.
4. Serialize GPU inference requests using an asynchronous-compatible lock or worker queue.
5. Avoid concurrent GPU inference that could exhaust VRAM.
6. Handle CUDA out-of-memory errors gracefully.
7. Do not silently switch to another model.
8. Keep CPU fallback available.

Do not change the current sliding-window inference configuration without testing and documenting the impact.

## 10. File Storage

Use local storage initially.

Suggested structure:

```text
backend/storage/
│
├── uploads/
│   └── patient_id/
│       └── original_mri.nii.gz
│
└── results/
    └── patient_id/
        ├── prediction.nii.gz
        ├── WT.nii.gz
        ├── TC.nii.gz
        ├── ET.nii.gz
        ├── comparison.png
        ├── axial_enhanced.png
        ├── coronal_enhanced.png
        ├── sagittal_enhanced.png
        └── result.json
```

Use generated safe patient/job identifiers.

Do not use user-provided filenames directly as storage paths.

Validate file sizes and formats. Prevent path traversal. Store uploaded medical data outside publicly accessible static directories.

Do not overwrite another patient's results.

## 11. Frontend Integration

Use:

- React
- Vite
- TypeScript
- Tailwind CSS
- Axios or Fetch API
- Recharts for metric visualizations if useful

Suggested dashboard sections:

1. Overview dashboard.
2. MRI upload.
3. Patient/job management.
4. MRI viewer.
5. Original MRI and enhanced MRI comparison.
6. Tumor segmentation visualization.
7. WT, TC and ET results.
8. Evaluation metrics.
9. Processing information.
10. Download center.

The frontend should display:
- Original MRI.
- Ground-truth comparison when available.
- AI segmentation overlay.
- Axial, coronal and sagittal views.
- Enhanced MRI previews.
- Dice, IoU, precision and recall when ground truth exists.
- Model name and inference device.
- Processing time.
- Downloadable NIfTI masks and result JSON.

Clearly distinguish actual ground truth from AI predictions.

Do not display fabricated metrics when ground truth is absent.

## 12. Result JSON

The existing result manager produces a JSON record containing:

- Project name
- Patient ID
- Timestamp
- Status
- Model
- Device
- Processing time
- Prediction path
- Individual mask paths
- Volume dimensions
- Tumor voxel counts
- Optional evaluation metrics
- Visualization information

The backend should convert local filesystem paths into secure API URLs before sending responses to the frontend.

Do not expose arbitrary server filesystem paths to clients.

## 13. Error Handling

The backend must handle:

- Missing MRI file.
- Invalid NIfTI file.
- Incorrect dimensions.
- Missing modalities.
- Invalid intensity values.
- Unsupported labels.
- Ground-truth dimension mismatch.
- Affine mismatch.
- Model loading failure.
- CUDA memory errors.
- Inference failure.
- Visualization failure.
- Storage failure.

Return clear HTTP error responses without exposing internal stack traces or sensitive server paths.

## 14. Medical and Research Disclaimer

NeuroVision is an educational and research prototype.

It is not a clinically validated diagnostic system.

Do not:
- Claim that it diagnoses brain cancer.
- Claim that it replaces radiologists.
- Present predictions as confirmed medical findings.
- Recommend treatment from segmentation outputs.
- Claim clinical accuracy based on one test case.

Display a clear disclaimer in the frontend.

## 15. Final Development Instructions

Build the FastAPI backend and React frontend around the existing AI engine.

Before implementing anything:

1. Inspect the existing project structure.
2. Read this integration guide.
3. Inspect the existing AI modules.
4. Preserve all existing working functionality.
5. Avoid duplicate implementations.
6. Keep the AI engine independent.
7. Use the existing pretrained model only.
8. Test backend endpoints against the real `BRATS_001` dataset.
9. Verify that uploaded MRI files can be processed and stored.
10. Verify that frontend images and downloadable outputs work.

Do not modify or replace pretrained model weights.

**Primary objective:** Build a professional NeuroVision application around the already implemented and tested AI engine, not rebuild the AI engine itself.
