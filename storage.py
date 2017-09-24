import psycopg2

class Storage:
    '''Key-value storage using the PostgreSQL database with a
    dictionary-like interface'''

    def __init__(self, host: str, dbname: str, user: str, password: str):
        '''Establishes a database connection, creates a table if necessary'''
        self.db = psycopg2.connect(host=host,
                                   dbname=dbname,
                                   user=user,
                                   password=password)
        c = self.db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS storage (key text,
                                                         value text)''')
        self.db.commit()
        c.close()

    def get(self, key: str) -> str:
        '''Returns a value by key given as a string'''
        c = self.db.cursor()
        c.execute('''SELECT FROM storage WHERE key = %s''', (key,))
        value = c.fetchone()[0]
        c.close()
        return value

    def set(self, key: str, value: str):
        '''Sets the given key to the given value'''
        c = self.db.cursor()
        c.execute('''UPDATE storage SET value = %s
                     WHERE key = %s''', (key, value))
        self.db.commit()
        c.close()

    def __getitem__(self, key: str) -> str:
        return self.get(key)

    def __setitem__(self, key: str, value: str):
        self.set(key, value)
