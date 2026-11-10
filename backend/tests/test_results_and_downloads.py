import sys
import io
import json
import zipfile
import shutil
import unittest
import uuid
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings


class TestResultsAndDownloads(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_job_id = str(uuid.uuid4())
        cls.job_dir = settings.results_dir / cls.test_job_id
        cls.job_dir.mkdir(parents=True, exist_ok=True)

        # Populate realistic test artifacts
        cls.result_data = {
            "project": "NeuroVision",
            "job_id": cls.test_job_id,
            "patient_id": "test_patient",
            "status": "completed",
            "model": "MONAI SegResNet",
            "device": "cuda",
            "processing_time_seconds": 1.75,
            "tumor_voxels": 12000,
            "region_voxels": {
                "WT": 12000,
                "TC": 6000,
                "ET": 3000
            },
            "shape": [240, 240, 155]
        }
        with (cls.job_dir / "result.json").open("w", encoding="utf-8") as f:
            json.dump(cls.result_data, f, indent=4)

        (cls.job_dir / "comparison.png").write_bytes(b"\x89PNG\r\n\x1a\nTEST_PNG_DATA")
        (cls.job_dir / "WT.nii.gz").write_bytes(b"GZIP_WT_MASK")
        (cls.job_dir / "TC.nii.gz").write_bytes(b"GZIP_TC_MASK")
        (cls.job_dir / "ET.nii.gz").write_bytes(b"GZIP_ET_MASK")
        (cls.job_dir / "prediction.nii.gz").write_bytes(b"GZIP_PRED")
        (cls.job_dir / "axial_enhanced.png").write_bytes(b"\x89PNG\r\n\x1a\nTEST_AXIAL")

    @classmethod
    def tearDownClass(cls):
        if cls.job_dir.exists():
            shutil.rmtree(cls.job_dir, ignore_errors=True)

    def test_nonexistent_job_results_404(self):
        random_uuid = str(uuid.uuid4())
        response = self.client.get(f"/api/results/{random_uuid}")
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_job_visualization_404(self):
        random_uuid = str(uuid.uuid4())
        response = self.client.get(f"/api/results/{random_uuid}/visualization")
        self.assertEqual(response.status_code, 404)

    def test_invalid_region_name_404(self):
        response = self.client.get(f"/api/results/{self.test_job_id}/masks/INVALID_REGION")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Unsupported mask region", response.json()["detail"])

    def test_get_results_json(self):
        response = self.client.get(f"/api/results/{self.test_job_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["job_id"], self.test_job_id)
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["tumor_voxels"], 12000)

    def test_get_visualization_png(self):
        response = self.client.get(f"/api/results/{self.test_job_id}/visualization")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG"))

    def test_get_individual_masks(self):
        for region in ["WT", "TC", "ET"]:
            response = self.client.get(f"/api/results/{self.test_job_id}/masks/{region}")
            self.assertEqual(response.status_code, 200)
            self.assertIn("application/gzip", response.headers["content-type"])
            self.assertIn(f"{self.test_job_id}_{region}.nii.gz", response.headers["content-disposition"])

    def test_get_enhanced_preview(self):
        response = self.client.get(f"/api/results/{self.test_job_id}/previews/axial")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")

    def test_download_zip_archive(self):
        response = self.client.get(f"/api/results/{self.test_job_id}/download")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/zip")
        self.assertIn(f"neurovision_results_{self.test_job_id}.zip", response.headers["content-disposition"])

        # Unpack and verify zip contents
        zip_buf = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buf, "r") as zf:
            file_list = zf.namelist()
            self.assertIn("result.json", file_list)
            self.assertIn("comparison.png", file_list)
            self.assertIn("WT.nii.gz", file_list)
            self.assertIn("TC.nii.gz", file_list)
            self.assertIn("ET.nii.gz", file_list)
            self.assertIn("prediction.nii.gz", file_list)
            self.assertIn("axial_enhanced.png", file_list)

    def test_persistence_after_simulated_restart(self):
        # Create a new TestClient instance to simulate a fresh client connection / server reboot
        new_client = TestClient(app)
        response = new_client.get(f"/api/results/{self.test_job_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["job_id"], self.test_job_id)


if __name__ == "__main__":
    unittest.main()
