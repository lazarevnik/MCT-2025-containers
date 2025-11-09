import pytest
import os
from unittest.mock import patch, MagicMock
import sys

sys.path.append('..')
from init_db import Visit, Base, main


class TestInitDB:

    def test_visit_model_attributes(self):
        visit = Visit()

        assert hasattr(visit, 'id')
        assert hasattr(visit, 'ip_address')
        assert hasattr(visit, '__tablename__')

    def test_visit_model_with_ip(self):
        test_ip = "192.168.1.100"
        visit = Visit(ip_address=test_ip)

        assert visit.ip_address == test_ip
        assert visit.id is None

    def test_visit_model_inheritance(self):
        assert issubclass(Visit, Base)

    @patch.dict(
        os.environ,
        {
            'POSTGRES_USER': 'test_user',
            'POSTGRES_PASSWORD': 'test_pass',
            'POSTGRES_HOST': 'test_host',
            'POSTGRES_PORT': '5433',
            'POSTGRES_DB': 'test_db',
        },
    )
    def test_environment_variables_loading(self):
        import importlib
        import init_db

        importlib.reload(init_db)

        assert init_db.DB_USER == 'test_user'
        assert init_db.DB_PASS == 'test_pass'
        assert init_db.DB_HOST == 'test_host'
        assert init_db.DB_PORT == '5433'
        assert init_db.DB_NAME == 'test_db'

    def test_default_environment_variables(self):
        from init_db import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

        assert DB_USER is not None
        assert DB_PASS is not None
        assert DB_HOST is not None
        assert DB_PORT is not None
        assert DB_NAME is not None

    @patch('init_db.Base.metadata.create_all')
    @patch('init_db.create_engine')
    def test_main_function_creates_engine(self, mock_create_engine, mock_create_all):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        main()

        mock_create_engine.assert_called_once()

        mock_create_all.assert_called_once_with(bind=mock_engine)

    @patch('init_db.Base.metadata.create_all')
    @patch('init_db.create_engine')
    def test_main_function_creates_tables(self, mock_create_engine, mock_create_all):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        main()

        mock_create_all.assert_called_once_with(bind=mock_engine)

    def test_visit_model_column_types(self):
        from sqlalchemy import Integer, String

        id_column = Visit.__table__.columns['id']
        ip_column = Visit.__table__.columns['ip_address']

        assert isinstance(id_column.type, Integer)
        assert isinstance(ip_column.type, String)

        assert id_column.primary_key is True
        assert id_column.autoincrement is True

    def test_visit_model_table_structure(self):
        table = Visit.__table__

        assert table.name == 'visits'

        column_names = [col.name for col in table.columns]
        assert len(column_names) == 2
        assert 'id' in column_names
        assert 'ip_address' in column_names


if __name__ == '__main__':
    pytest.main([__file__])
