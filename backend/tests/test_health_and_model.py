import sys
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app


class TestHealthAndModelEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("project"), "NeuroVision")
        self.assertIn("health_url", data)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertTrue(data.get("ai_engine_available"))
        self.assertIn("model_loaded", data)
        self.assertIn("device", data)
        self.assertIn("cuda_available", data)

    def test_model_info_endpoint(self):
        response = self.client.get("/api/model-info")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("model_name"), "MONAI SegResNet")
        self.assertEqual(data.get("architecture"), "SegResNet")
        self.assertEqual(data.get("bundle"), "brats_mri_segmentation")
        self.assertEqual(data.get("version"), "0.5.2")
        self.assertEqual(data.get("parameters"), 4702227)
        self.assertEqual(data.get("input_channels"), 4)
        self.assertEqual(data.get("output_channels"), 3)
        self.assertEqual(data.get("status"), "loaded")
        self.assertTrue(data.get("training_disabled"))
        self.assertTrue(data.get("fine_tuning_disabled"))
        self.assertTrue(data.get("cached"))


if __name__ == "__main__":
    unittest.main()
