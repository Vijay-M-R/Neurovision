# NeuroVision — Python FastAPI Backend

NeuroVision Medical Image Processing System for Brain MRI Enhancement and Multi-Region Tumor Segmentation.

This backend provides a high-performance, asynchronous REST API integrating the existing NeuroVision AI engine (MONAI SegResNet pretrained model) with secure file management, GPU concurrency serialization, and structured clinical artifact downloads.

---

## 1. System Architecture

```text
neurovision/
├── ai_engine/                  # Protected AI Engine (MONAI SegResNet, Preprocessing, Enhancement)
├── pretrained_models/          # Pretrained bundle (brats_mri_segmentation v0.5.2)
├── Task01_BrainTumour/         # Validation dataset (BRATS_001.nii.gz, etc.)
├── outputs/                    # Reference baseline outputs (protected)
│
└── backend/
    ├── app/
    │   ├── main.py             # FastAPI entry point, lifespan, CORS, and router mounting
    │   ├── config.py           # Application settings, environment variables, storage paths
    │   │
    │   ├── routes/
    │   │   ├── health.py       # GET /api/health
    │   │   ├── model_info.py   # GET /api/model-info
    │   │   ├── upload.py       # POST /api/upload
    │   │   ├── segmentation.py # POST /api/segment/{job_id}
    │   │   ├── enhancement.py  # POST /api/enhance/{job_id}
    │   │   └── results.py      # GET /api/results/{job_id}, /visualization, /masks/{region}, /download
    │   │
    │   ├── services/
    │   │   ├── ai_service.py   # Thread-safe GPU inference lock & run_pipeline caller
    │   │   ├── file_service.py # Chunked streaming upload, NIfTI validation, job isolation
    │   │   └── result_service.py # Artifact normalization, URL transformation, metadata persistence
    │   │
    │   ├── schemas/
    │   │   ├── request.py      # Request schemas (EnhanceRequest, SegmentRequest)
    │   │   └── response.py     # Response schemas (HealthResponse, ModelInfoResponse, etc.)
    │   │
    │   └── utils/
    │       └── errors.py       # Custom HTTP exception handlers and error classes
    │
    ├── storage/                # Local filesystem storage (gitignored)
    │   ├── uploads/{job_id}/   # Original MRI and upload metadata
    │   └── results/{job_id}/   # Segmentation masks, visualization PNG, enhanced previews, result.json
    │
    ├── tests/                  # Automated test suite (unit, API, and GPU integration)
    ├── requirements.txt        # Backend dependencies
    ├── .env.example            # Environment variables template
    └── README.md
```

---

## 2. Dependencies & Hardware Requirements

### Compute Hardware
- **GPU:** NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM) or equivalent CUDA GPU.
- **CPU Fallback:** Fully supported when CUDA is unavailable.

### Environment & Packages
- Python 3.11+
- PyTorch 2.4.1+cu121
- MONAI 1.4.0
- NiBabel 5.4.2
- OpenCV 4.10.0+
- FastAPI 0.115.0+
- Uvicorn 0.30.0+
- Pydantic 2.8.0+
- Python-Multipart 0.0.9+

All dependencies are installed in the existing virtual environment:
`C:\Users\Vijay M R\neurovision\venv`

---

## 3. Configuration & Environment Variables

Settings are configured via `backend/.env` or system environment variables:

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Application runtime environment |
| `HOST` | `127.0.0.1` | Server listening host |
| `PORT` | `8000` | Server listening port |
| `FRONTEND_ORIGIN` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed CORS origins for React frontend |
| `MAX_UPLOAD_SIZE_MB` | `150` | Maximum allowable MRI upload file size (MB) |
| `STORAGE_ROOT` | `backend/storage` | Root path for isolated uploads and results |

---

## 4. Startup Commands

Activate the virtual environment and start the Uvicorn ASGI server from the project root:

```powershell
# From project root: C:\Users\Vijay M R\neurovision
.\venv\Scripts\Activate.ps1

# Run Uvicorn development server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API documentation will be available at:
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 5. API Endpoints

### Health & Metadata
- **`GET /api/health`**
  - Returns backend readiness, device information (`cuda`/`cpu`), CUDA availability, and SegResNet cache status without running inference.
- **`GET /api/model-info`**
  - Returns real MONAI SegResNet metadata (architecture, 4,702,227 parameters, 4 input channels, 3 output channels, training/fine-tuning disabled flags).

### MRI Upload
- **`POST /api/upload`**
  - Accepts multipart file upload (`.nii` or `.nii.gz`).
  - Enforces file size limits via streaming chunk processing.
  - Validates NIfTI format and 4D four-modality shape `(X, Y, Z, 4)`.
  - Rejects zero-filled or corrupted channels.
  - Returns: `job_id` (UUID), `filename`, `dimensions`, `modalities`.

### AI Processing
- **`POST /api/segment/{job_id}`**
  - Executes full multi-region tumor segmentation using the existing AI pipeline (`ai_engine.pipeline.run_pipeline`).
  - Serialized by an `asyncio.Lock` to guarantee safe 6 GB VRAM GPU allocation without concurrency conflicts.
  - Offloaded to thread pool (`run_in_threadpool`) so event loop remains non-blocking.
  - Returns: `regions` (WT, TC, ET voxel counts), `tumor_voxels`, `processing_time_seconds`, and resource URLs.
- **`POST /api/enhance/{job_id}`**
  - Generates CLAHE contrast-enhanced slice previews (`axial`, `coronal`, `sagittal`) for the selected modality.
  - Independent operation that never touches the segmentation input or alters the original MRI.

### Results & Artifacts
- **`GET /api/results/{job_id}`**
  - Returns complete analysis result JSON with secure API URLs replacing server filesystem paths.
- **`GET /api/results/{job_id}/visualization`**
  - Serves the high-resolution 3x3 orthogonal comparison PNG.
- **`GET /api/results/{job_id}/masks/{region}`**
  - Serves individual binary mask NIfTI volumes for `WT`, `TC`, or `ET`.
- **`GET /api/results/{job_id}/previews/{view}`**
  - Serves enhanced slice previews for `axial`, `coronal`, or `sagittal` views.
- **`GET /api/results/{job_id}/download`**
  - Generates and streams a structured ZIP archive containing:
    - `prediction.nii.gz` (combined multi-label map)
    - `WT.nii.gz` (Whole Tumor mask)
    - `TC.nii.gz` (Tumor Core mask)
    - `ET.nii.gz` (Enhancing Tumor mask)
    - `comparison.png` (orthogonal viewer)
    - `axial_enhanced.png`, `coronal_enhanced.png`, `sagittal_enhanced.png` (if generated)
    - `result.json` (analysis metadata)

---

## 6. MRI Input Specifications

The backend strictly enforces the AI engine's input format:
- **Format:** Single 4D NIfTI file (`.nii` or `.nii.gz`).
- **Dimensions:** `(X, Y, Z, 4)`.
- **Required Channel Order:**
  1. Channel 0: FLAIR
  2. Channel 1: T1
  3. Channel 2: T1ce
  4. Channel 3: T2
- The preprocessor automatically converts this to model order `[T1ce, T1, T2, FLAIR]` and normalizes intensities.

---

## 7. Storage Structure

Job data is stored in isolated directories using UUIDs:

```text
backend/storage/
├── uploads/
│   └── {job_id}/
│       ├── original_mri.nii.gz
│       └── metadata.json
│
└── results/
    └── {job_id}/
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

Results survive server restarts and persist on the filesystem.

---

## 8. Error Handling & HTTP Status Codes

The API returns consistent error JSON (`{"detail": "..."}`) without exposing internal paths or stack traces:

- **400 Bad Request:** Unsupported file extension or invalid request parameters.
- **404 Not Found:** Job ID or requested mask/result does not exist.
- **413 Content Too Large:** Uploaded file exceeds the configured size limit.
- **422 Unprocessable Content:** File is corrupt, dimensions are not 4D, or modalities contain all zeros.
- **500 Internal Server Error:** Unexpected server-side failure.
- **503 Service Unavailable:** AI model unavailable or GPU out-of-memory.

---

## 9. Testing & Verification

Run the complete automated test suite using Python's built-in `unittest`:

```powershell
# Run all unit, API, and GPU integration tests
.\venv\Scripts\python.exe -m unittest discover -s backend/tests
```

Individual test modules:
```powershell
# 1. Health and model info endpoints
.\venv\Scripts\python.exe -m unittest backend.tests.test_health_and_model

# 2. Upload and validation endpoints
.\venv\Scripts\python.exe -m unittest backend.tests.test_upload

# 3. Enhancement and error rejection
.\venv\Scripts\python.exe -m unittest backend.tests.test_enhancement_and_segmentation

# 4. Results, masks, and ZIP downloads
.\venv\Scripts\python.exe -m unittest backend.tests.test_results_and_downloads

# 5. Full GPU end-to-end integration test (RTX 4050 GPU on BRATS_001)
.\venv\Scripts\python.exe -m unittest backend.tests.test_gpu_integration
```
