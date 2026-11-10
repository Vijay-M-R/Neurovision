import sys
import io
import json
import shutil
import zipfile
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings

BRATS_001_PATH = PROJECT_ROOT / "Task01_BrainTumour" / "imagesTr" / "BRATS_001.nii.gz"


class TestGPUIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.job_id = None

    @classmethod
    def tearDownClass(cls):
        # Clean up test directories created during this integration run
        if cls.job_id:
            up_dir = settings.uploads_dir / cls.job_id
            res_dir = settings.results_dir / cls.job_id
            if up_dir.exists():
                shutil.rmtree(up_dir, ignore_errors=True)
            if res_dir.exists():
                shutil.rmtree(res_dir, ignore_errors=True)

    def test_full_pipeline_gpu_integration(self):
        self.assertTrue(BRATS_001_PATH.is_file(), f"BRATS_001 not found at {BRATS_001_PATH}")

        # 1. Upload real MRI scan
        with BRATS_001_PATH.open("rb") as f:
            upload_resp = self.client.post(
                "/api/upload",
                files={"file": ("BRATS_001.nii.gz", f, "application/gzip")}
            )

        self.assertEqual(upload_resp.status_code, 201)
        up_data = upload_resp.json()
        self.__class__.job_id = up_data["job_id"]
        job_id = self.job_id

        self.assertEqual(up_data["status"], "uploaded")
        self.assertEqual(up_data["dimensions"], [240, 240, 155, 4])
        self.assertEqual(up_data["modalities"], 4)

        # 2. Run real GPU segmentation
        seg_resp = self.client.post(f"/api/segment/{job_id}")
        self.assertEqual(seg_resp.status_code, 200)
        seg_data = seg_resp.json()

        self.assertEqual(seg_data["status"], "completed")
        self.assertEqual(seg_data["model"], "MONAI SegResNet")
        self.assertIn("cuda", seg_data["device"].lower())
        self.assertGreater(seg_data["processing_time_seconds"], 0.0)

        # Verify real tumor segmentation voxel counts match the pretrained SegResNet benchmark
        regions = seg_data["regions"]
        self.assertAlmostEqual(regions["WT"], 136299, delta=500)
        self.assertAlmostEqual(regions["TC"], 61641, delta=500)
        self.assertAlmostEqual(regions["ET"], 34330, delta=500)

        # 3. Check artifacts on disk in backend/storage/results/{job_id}
        result_dir = settings.results_dir / job_id
        self.assertTrue((result_dir / "prediction.nii.gz").is_file())
        self.assertTrue((result_dir / "WT.nii.gz").is_file())
        self.assertTrue((result_dir / "TC.nii.gz").is_file())
        self.assertTrue((result_dir / "ET.nii.gz").is_file())
        self.assertTrue((result_dir / "comparison.png").is_file())
        self.assertTrue((result_dir / "result.json").is_file())

        # 4. Run contrast enhancement
        enh_resp = self.client.post(
            f"/api/enhance/{job_id}",
            json={"modality": 0, "clip_limit": 2.0}
        )
        self.assertEqual(enh_resp.status_code, 200)
        enh_data = enh_resp.json()
        self.assertEqual(enh_data["status"], "completed")
        self.assertEqual(enh_data["modality"], "FLAIR")
        self.assertTrue((result_dir / "axial_enhanced.png").is_file())
        self.assertTrue((result_dir / "coronal_enhanced.png").is_file())
        self.assertTrue((result_dir / "sagittal_enhanced.png").is_file())

        # 5. Retrieve visualization
        vis_resp = self.client.get(f"/api/results/{job_id}/visualization")
        self.assertEqual(vis_resp.status_code, 200)
        self.assertEqual(vis_resp.headers["content-type"], "image/png")

        # 6. Retrieve individual mask
        mask_resp = self.client.get(f"/api/results/{job_id}/masks/WT")
        self.assertEqual(mask_resp.status_code, 200)
        self.assertIn("application/gzip", mask_resp.headers["content-type"])

        # 7. Download complete ZIP bundle
        zip_resp = self.client.get(f"/api/results/{job_id}/download")
        self.assertEqual(zip_resp.status_code, 200)
        self.assertEqual(zip_resp.headers["content-type"], "application/zip")

        zip_buf = io.BytesIO(zip_resp.content)
        with zipfile.ZipFile(zip_buf, "r") as zf:
            files_in_zip = zf.namelist()
            for expected_file in [
                "prediction.nii.gz",
                "WT.nii.gz",
                "TC.nii.gz",
                "ET.nii.gz",
                "comparison.png",
                "axial_enhanced.png",
                "coronal_enhanced.png",
                "sagittal_enhanced.png",
                "result.json"
            ]:
                self.assertIn(expected_file, files_in_zip)

        # 8. Check persistence: simulate server restart by querying with a fresh client
        fresh_client = TestClient(app)
        res_resp = fresh_client.get(f"/api/results/{job_id}")
        self.assertEqual(res_resp.status_code, 200)
        persisted_data = res_resp.json()
        self.assertEqual(persisted_data["job_id"], job_id)
        self.assertEqual(persisted_data["status"], "completed")


if __name__ == "__main__":
    unittest.main()
