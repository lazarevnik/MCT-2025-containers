from unittest.mock import patch
from psycopg2 import sql
from web.psql import add_ip_request, requests_count

class TestPsql:

    @patch("web.psql.make_request")
    def test_add_ip_req_query(self, mocked_make_req):
        ip = "10.20.30.255"
        add_ip_request(ip)
        expected_query = "INSERT INTO ips (ip) VALUES (%s)"
        mocked_make_req.assert_called_once_with(expected_query, (ip,), fetch=False)

    @patch("web.psql.make_request", return_value=100)
    def test_requests_count(self, mocked_make_req):
        table_name = "some_table"
        count = requests_count(table_name)
        expected_query = sql.SQL("SELECT COUNT(*) FROM {}").format(
            sql.Identifier(table_name)
        )
        mocked_make_req.assert_called_once_with(expected_query)
        assert count == 100
