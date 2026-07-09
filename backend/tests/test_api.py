import json
import unittest
import sys
import os

# Adjust path to find backend modules first
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_path)

from app import app

class TestFitnessAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_endpoint(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['app'], 'AI Fitness & Diet Recommendation API')
        self.assertEqual(data['status'], 'running')

    def test_health_endpoint(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertTrue(data['models_loaded'])

    def test_predict_endpoint_success(self):
        payload = {
            "name": "Jane Doe",
            "age": 25,
            "gender": "Female",
            "height": 165.0,
            "weight": 60.0,
            "sleep": 8.0,
            "steps": 12000,
            "workout_hours": 2.0,
            "goal": "Cut",
            "diet_pref": "High Protein",
            "medical": "None"
        }
        response = self.app.post('/predict', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Jane Doe')
        self.assertIn('bmi', data)
        self.assertEqual(data['bmi_status'], 'Normal Weight')
        self.assertIn('ml_calories', data)
        self.assertIn('bmr_calories', data)
        self.assertIn('workout_plan', data)
        self.assertIn('meal_plan', data)
        self.assertIn('protein_g', data)
        self.assertIn('carb_g', data)
        self.assertIn('fat_g', data)
        self.assertIn('weight_history', data)
        self.assertIn('lstm_next_weight', data)
        self.assertEqual(len(data['projection_weights']), 5)

    def test_predict_endpoint_missing_fields(self):
        # Missing 'weight'
        payload = {
            "name": "Jane Doe",
            "age": 25,
            "gender": "Female",
            "height": 165.0,
            "sleep": 8.0,
            "steps": 12000,
            "workout_hours": 2.0,
            "goal": "Cut",
            "diet_pref": "High Protein",
            "medical": "None"
        }
        response = self.app.post('/predict', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertTrue('Missing required field' in data['error'])

    def test_predict_endpoint_invalid_values(self):
        # Age out of bounds (9)
        payload = {
            "name": "Jane Doe",
            "age": 9,
            "gender": "Female",
            "height": 165.0,
            "weight": 60.0,
            "sleep": 8.0,
            "steps": 12000,
            "workout_hours": 2.0,
            "goal": "Cut",
            "diet_pref": "High Protein",
            "medical": "None"
        }
        response = self.app.post('/predict', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Age must be between 10 and 80')

        # Invalid Gender
        payload["age"] = 25
        payload["gender"] = "Other"
        response = self.app.post('/predict', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], "Gender must be 'Male' or 'Female'")

if __name__ == '__main__':
    unittest.main()
