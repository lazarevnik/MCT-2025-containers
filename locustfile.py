from locust import HttpUser, task, between
import random

class AppUser(HttpUser):
    wait_time = between(1, 3)
    @task(5)
    def visit_home(self):
        self.client.get("/")
    @task(3)
    def ping_endpoint(self):
        self.client.get("/ping")
    @task(2)
    def get_visits(self):
        self.client.get("/visits")
