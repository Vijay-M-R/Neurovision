import sys
import io
import shutil
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import gzip
import numpy as np
import nibabel as nib
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings


def create_nifti_bytes(shape, zero_channel=None):
    """Helper to create an in-memory NIfTI .nii.gz file."""
    data = np.ones(shape, dtype=np.float32) * 100.0
    if zero_channel is not None and len(shape) == 4:
        data[..., zero_channel] = 0.0
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    bio = io.BytesIO()
    file_map = img.make_file_map()
    file_map['image'].fileobj = bio
    img.to_file_map(file_map)
    raw_nii = bio.getvalue()
    return gzip.compress(raw_nii)


class TestUploadEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.created_jobs = []

    @classmethod
    def tearDownClass(cls):
        # Clean up test upload folders
        for job_id in cls.created_jobs:
            job_dir = settings.uploads_dir / job_id
            if job_dir.exists():
                shutil.rmtree(job_dir, ignore_errors=True)

    def test_valid_4d_nifti_upload(self):
        nii_bytes = create_nifti_bytes((12, 12, 10, 4))
        response = self.client.post(
            "/api/upload",
            files={"file": ("brain_scan.nii.gz", nii_bytes, "application/gzip")}
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "uploaded")
        self.assertEqual(data["modalities"], 4)
        self.assertEqual(data["dimensions"], [12, 12, 10, 4])
        self.assertEqual(data["filename"], "original_mri.nii.gz")
        self.assertIn("job_id", data)
        self.created_jobs.append(data["job_id"])

        # Check directory and metadata
        job_dir = settings.uploads_dir / data["job_id"]
        self.assertTrue((job_dir / "original_mri.nii.gz").exists())
        self.assertTrue((job_dir / "metadata.json").exists())

    def test_invalid_extension_rejection(self):
        response = self.client.post(
            "/api/upload",
            files={"file": ("notes.txt", b"plain text data", "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Only .nii and .nii.gz", response.json()["detail"])

    def test_corrupt_nifti_rejection(self):
        response = self.client.post(
            "/api/upload",
            files={"file": ("corrupt.nii.gz", b"GARBAGE_NOT_NIFTI_BYTES", "application/gzip")}
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("Corrupt or unreadable", response.json()["detail"])

    def test_incorrect_3d_dimensions_rejection(self):
        # 3D image instead of 4D
        nii_3d = create_nifti_bytes((12, 12, 10))
        response = self.client.post(
            "/api/upload",
            files={"file": ("scan_3d.nii.gz", nii_3d, "application/gzip")}
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("Expected a 4D MRI", response.json()["detail"])

    def test_incorrect_channel_count_rejection(self):
        # 4D image but with 3 channels instead of 4
        nii_3ch = create_nifti_bytes((12, 12, 10, 3))
        response = self.client.post(
            "/api/upload",
            files={"file": ("scan_3ch.nii.gz", nii_3ch, "application/gzip")}
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("Expected 4 modalities", response.json()["detail"])

    def test_zero_modality_rejection(self):
        # 4D image where channel 2 is all zeros
        nii_zero_ch = create_nifti_bytes((12, 12, 10, 4), zero_channel=2)
        response = self.client.post(
            "/api/upload",
            files={"file": ("zero_channel.nii.gz", nii_zero_ch, "application/gzip")}
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("contains only zeros", response.json()["detail"])

    def test_oversized_upload_rejection(self):
        # Temporarily set max_upload_size_mb to a tiny value to verify enforcement
        original_mb = settings.max_upload_size_mb
        try:
            settings.max_upload_size_mb = 1  # 1 MB
            oversized_data = b"0" * (2 * 1024 * 1024)  # 2 MB
            response = self.client.post(
                "/api/upload",
                files={"file": ("huge.nii.gz", oversized_data, "application/gzip")}
            )
            self.assertEqual(response.status_code, 413)
            self.assertIn("exceeds maximum allowed size", response.json()["detail"])
        finally:
            settings.max_upload_size_mb = original_mb


if __name__ == "__main__":
    unittest.main()
