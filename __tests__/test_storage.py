import os
import unittest
from urllib.parse import urlparse
import psycopg2
from storage import Storage


class TestStorage(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        url = urlparse(os.environ['TEST_DATABASE_URL'])
        self.TEST_HOST = url.hostname
        self.TEST_NAME = url.path[1:]
        self.TEST_USER = url.username
        self.TEST_PSWD = url.password
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.storage = Storage(host=self.TEST_HOST,
                               dbname=self.TEST_NAME,
                               user=self.TEST_USER,
                               password=self.TEST_PSWD)
        self.db = psycopg2.connect(host=self.TEST_HOST,
                                   dbname=self.TEST_NAME,
                                   user=self.TEST_USER,
                                   password=self.TEST_PSWD)

    def tearDown(self):
        c = self.db.cursor()
        c.execute('''DELETE FROM storage''')
        self.db.commit()
        c.close()
        self.db.close()
        self.storage.close()

    def test_get(self):
        c = self.db.cursor()
        c.execute('''INSERT INTO storage
                     VALUES ('getkey', '["value"]')''')
        self.db.commit()
        c.close()

        self.assertEqual(self.storage.get('getkey'),
                         '["value"]')

        self.assertEqual(self.storage['getkey'],
                         '["value"]')

    def test_set(self):
        c = self.db.cursor()

        self.storage.set('setkey', '["value"]')
        c.execute('''SELECT value FROM storage WHERE key = 'setkey' ''')
        self.assertEqual(c.fetchone()[0],
                         '["value"]')

        self.storage['setkey'] = '["new","value"]'
        c.execute('''SELECT value FROM storage WHERE key = 'setkey' ''')
        self.assertEqual(c.fetchone()[0],
                         '["new","value"]')

        self.db.commit()
        c.close()
