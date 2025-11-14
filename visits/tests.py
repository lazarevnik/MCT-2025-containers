from django.test import TestCase, Client
from .models import Visit

class PingVisitsTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_ping_creates_visit(self):
        response = self.client.get('/ping')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'pong')
        self.assertEqual(Visit.objects.count(), 1)

    def test_visits_returns_count(self):
        Visit.objects.create(ip='127.0.0.1')
        Visit.objects.create(ip='192.168.0.1')
        response = self.client.get('/visits')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), '2')