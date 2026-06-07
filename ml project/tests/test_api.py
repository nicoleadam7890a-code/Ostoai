import unittest
import sys
import os

# Add the parent directory to sys.path to import api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        """Test if the index route returns 200"""
        response = self.app.get('/')
        # Since / redirects to login.html or serves it, we check if it's successful
        self.assertEqual(response.status_code, 200)

    def test_invalid_login(self):
        """Test login with empty credentials"""
        response = self.app.post('/login', json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['status'], 'error')

if __name__ == '__main__':
    unittest.main()
