from unittest.mock import patch

class TestView:

    def test_default_route(self, client):
        response = client.get("/")
        assert response.status_code == 200

    @patch('web.views.add_ip_request')
    def test_ping(self, mock_add_ip_request, client):
        response = client.get("/ping", environ_base={'REMOTE_ADDR': '10.20.30.255'})
        assert response.status_code == 200
        assert response.data.decode() == "pong\n"
        mock_add_ip_request.assert_called_once_with("10.20.30.255")

    @patch('web.views.requests_count', return_value=100)
    def test_visits(self, mocked_req_count, client):
        response = client.get("/visits")
        assert response.status_code == 200
        assert response.data.decode() == "100\n"
