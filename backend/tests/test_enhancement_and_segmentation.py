import sys
import io
import gzip
import shutil
import unittest
import uuid
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import nibabel as nib
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings


def create_nifti_bytes(shape):
    data = np.ones(shape, dtype=np.float32) * 100.0
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    bio = io.BytesIO()
    file_map = img.make_file_map()
    file_map['image'].fileobj = bio
    img.to_file_map(file_map)
    return gzip.compress(bio.getvalue())


class TestEnhancementAndSegmentationRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.created_jobs = []

    @classmethod
    def tearDownClass(cls):
        for job_id in cls.created_jobs:
            up_dir = settings.uploads_dir / job_id
            res_dir = settings.results_dir / job_id
            if up_dir.exists():
                shutil.rmtree(up_dir, ignore_errors=True)
            if res_dir.exists():
                shutil.rmtree(res_dir, ignore_errors=True)

    def test_segment_invalid_job_id_format(self):
        response = self.client.post("/api/segment/not-a-uuid")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Invalid job ID format", response.json()["detail"])

    def test_segment_nonexistent_job_id(self):
        random_uuid = str(uuid.uuid4())
        response = self.client.post(f"/api/segment/{random_uuid}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("No upload found", response.json()["detail"])

    def test_enhance_invalid_job_id_format(self):
        response = self.client.post("/api/enhance/invalid-id-123")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Invalid job ID format", response.json()["detail"])

    def test_enhance_nonexistent_job_id(self):
        random_uuid = str(uuid.uuid4())
        response = self.client.post(f"/api/enhance/{random_uuid}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("No upload found", response.json()["detail"])

    def test_enhance_valid_upload(self):
        # 1. Upload small valid 4D MRI
        nii_bytes = create_nifti_bytes((16, 16, 16, 4))
        up_resp = self.client.post(
            "/api/upload",
            files={"file": ("brain_scan.nii.gz", nii_bytes, "application/gzip")}
        )
        self.assertEqual(up_resp.status_code, 201)
        job_id = up_resp.json()["job_id"]
        self.created_jobs.append(job_id)

        # 2. Call enhance
        enhance_resp = self.client.post(
            f"/api/enhance/{job_id}",
            json={"modality": 0, "clip_limit": 2.0}
        )
        self.assertEqual(enhance_resp.status_code, 200)
        data = enhance_resp.json()
        self.assertEqual(data["job_id"], job_id)
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["modality"], "FLAIR")
        self.assertIn("preview_urls", data)
        self.assertIn("axial", data["preview_urls"])
        self.assertIn("coronal", data["preview_urls"])
        self.assertIn("sagittal", data["preview_urls"])

        # 3. Check artifacts on disk in backend/storage/results/{job_id}
        res_dir = settings.results_dir / job_id
        self.assertTrue((res_dir / "axial_enhanced.png").exists())
        self.assertTrue((res_dir / "coronal_enhanced.png").exists())
        self.assertTrue((res_dir / "sagittal_enhanced.png").exists())


if __name__ == "__main__":
    unittest.main()
