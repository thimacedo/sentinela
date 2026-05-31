# tests/test_queue_manager.py
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.queue_manager import QueueManager
from models.target import Target

class DummyTable:
    def __init__(self, db):
        self.db = db
        self._data = None
        self._condition = None

    def update(self, data):
        # capture update data
        self.db.last_update_data = data
        return self

    def eq(self, key, value):
        # store condition if needed
        self._condition = (key, value)
        return self

    def execute(self):
        return self

    # Dummy methods for other calls used elsewhere (not needed for rotate_target)
    def select(self, *args, **kwargs):
        return self
    def eq(self, *args, **kwargs):
        return self
    def limit(self, *args, **kwargs):
        return self
    def on_conflict(self, *args, **kwargs):
        return self
    def upsert(self, *args, **kwargs):
        return self
    def filter(self, *args, **kwargs):
        return self
    def or_(self, *args, **kwargs):
        return self
    def order(self, *args, **kwargs):
        return self
    def execute(self):
        return self

class DummyDB:
    def __init__(self):
        self.last_update_data = None

    def table(self, name):
        return DummyTable(self)

class RotateTargetTest(unittest.TestCase):
    def setUp(self):
        self.db = DummyDB()
        self.qm = QueueManager(self.db)
        # Fixed current time for deterministic tests
        self.fixed_now = datetime(2026, 5, 31, 12, 0, 0, tzinfo=timezone.utc)

    def _run_rotate(self, target):
        with patch('core.queue_manager.datetime') as mock_dt:
            mock_dt.now.return_value = self.fixed_now
            mock_dt.timezone = timezone
            # also need isoformat method on datetime objects used in code
            mock_dt.fromisoformat = datetime.fromisoformat
            self.qm.rotate_target(target)
        return self.db.last_update_data['termometro']

    def test_no_posts_no_dates_results_in_morno(self):
        target = Target(username='user1', candidato_id='user1', source='test')
        target.post_metas = []
        term = self._run_rotate(target)
        self.assertEqual(term, 'MORNO')

    def test_no_comments_error_results_in_morno(self):
        target = Target(username='user2', candidato_id='user2', source='test')
        target.error = 'no_comments_found'
        target.post_metas = []
        term = self._run_rotate(target)
        self.assertEqual(term, 'MORNO')

    def test_recent_post_less_than_7_days_morno(self):
        target = Target(username='user3', candidato_id='user3', source='test')
        recent_date = (self.fixed_now - timedelta(days=3)).isoformat()
        target.post_metas = [{'timestamp': recent_date}]
        term = self._run_rotate(target)
        self.assertEqual(term, 'MORNO')

    def test_post_older_than_7_days_frio(self):
        target = Target(username='user4', candidato_id='user4', source='test')
        old_date = (self.fixed_now - timedelta(days=10)).isoformat()
        target.post_metas = [{'timestamp': old_date}]
        term = self._run_rotate(target)
        self.assertEqual(term, 'FRIO')

    def test_high_frequency_quente(self):
        target = Target(username='user5', candidato_id='user5', source='test')
        # create 5 posts spread over 5 days => frequency approx 5 posts/week
        dates = []
        for i in range(5):
            d = (self.fixed_now - timedelta(days=i)).isoformat()
            dates.append({'timestamp': d})
        target.post_metas = dates
        term = self._run_rotate(target)
        self.assertEqual(term, 'QUENTE')

if __name__ == '__main__':
    unittest.main()
