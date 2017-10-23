import json
import unittest
from diff_computer import DiffComputer, NoUpdate


class TestDiffComputer(unittest.TestCase):
    def setUp(self):
        self.storage = {}
        self.comp = DiffComputer(self.storage)

    def tearDown(self):
        del self.storage
        del self.comp

    def test_exchange(self):
        self.storage['key1'] = '{"some":"json"}'
        old1 = self.comp.exchange('key1', {'some': ['more', 'json']})
        self.assertDictEqual(json.loads(self.storage['key1']),
                             {'some': ['more', 'json']})
        self.assertDictEqual(old1,
                             {'some': 'json'})

        with self.assertRaises(NoUpdate):
            self.comp.exchange('key1', {'some': ['more', 'json']})

        old2 = self.comp.exchange('key2', ['smth', 'new'])
        self.assertIsNone(old2)
        self.assertEqual(self.storage['key2'],
                         '["smth","new"]')

        with self.assertRaises(NoUpdate):
            self.comp.exchange('key3', None)

    def test_class_list(self):
        self.storage['class_list'] = 'null'

        classes = {'8': ['8А', '8Б'],
                   '9': ['9А', '9Б']}
        diff1 = self.comp.diff_class_list(classes)
        self.assertDictEqual(json.loads(diff1),
                             classes)

        classes['9'].append('9В')
        diff2 = self.comp.diff_class_list(classes)
        self.assertDictEqual(json.loads(diff2),
                             {'8': None,
                              '9': ['9А', '9Б', '9В']})

    def test_study_plan(self):
        self.storage['study_plan'] = 'null'

        plan = [['september'], ['october']]

        diff1 = self.comp.diff_study_plan(plan)
        self.assertListEqual(json.loads(diff1),
                             plan)

        plan.append(['november'])
        diff2 = self.comp.diff_study_plan(plan)
        self.assertListEqual(json.loads(diff2),
                             [None, None, ['november']])


    def test_rings_timetable(self):
        self.storage['rings_timetable'] = 'null'

        rings = [{'type': 'lesson'}, {'type': 'break'}]

        diff1 = self.comp.diff_rings_timetable(rings)
        self.assertListEqual(json.loads(diff1),
                             rings)

        rings.append({'type': 'lesson'})
        diff2 = self.comp.diff_rings_timetable(rings)
        self.assertListEqual(json.loads(diff2),
                             rings)

    def test_timetable(self):
        old = [[['maths'], ['maths'], [], [], [], [], []],
               [['pe'],    ['pe'],    [], [], [], [], []],
               [['ict'],   ['ict'],   [], [], [], [], []]]

        new = [[['maths'], ['english'], [],      [], [], [], []],
               [['pe'],    [],          [],      [], [], [], []],
               [[],        ['ict'],     ['ict'], [], [], [], []]]

        act = [[None, ['english'], None,    None, None, None, None],
               [None, [],          None,    None, None, None, None],
               [[],   None,        ['ict'], None, None, None, None]]

        diff = self.comp.diff_timetable(old, new)
        self.assertListEqual(act,
                             diff)

    def test_full_perm_timetable(self):
        self.storage['full_perm_timetable'] = 'null'

        tmtbl = {'8А': [['lesson', 'lesson'], []]}

        diff1 = self.comp.diff_full_perm_timetable(tmtbl)
        self.assertDictEqual(json.loads(diff1),
                             tmtbl)

        tmtbl['8Б'] = []
        diff2 = self.comp.diff_full_perm_timetable(tmtbl)
        self.assertDictEqual(json.loads(diff2),
                             {'8А': [[None, None], []],
                              '8Б': []})

    def test_teachers(self):
        self.storage['teachers'] = 'null'

        tchrs = [{'abbr': 't1',
                  'full': 'Teacher 1',
                  'job': 'teacher',
                  'timetable': [],
                  'classes': []},
                 {'abbr': 't2'},
                 {'abbr': 't3'}]

        diff1 = self.comp.diff_teachers(tchrs)
        self.assertListEqual(json.loads(diff1),
                             tchrs)

        tchrs2 = [{'abbr': 't1',
                   'job': 'teacher',
                   'timetable': [],
                   'classes': []},
                  {'abbr': 't2'},
                  {'job': 'test_wrecker'}]
        diff2 = self.comp.diff_teachers(tchrs2)
        tchrs[0]['job'] = None
        self.assertListEqual(json.loads(diff2),
                             [{'abbr': 't1',
                               'job': None,
                               'timetable': [],
                               'classes': None},
                              {'abbr': 't2'},
                              {'job': 'test_wrecker'}])

    def test_vacant_rooms(self):
        self.storage['vacant_rooms'] = 'null'

        vacant = [[{'1': ['101', '102']}, {}, {}, {}, {}], [], [], [], [], []]
        diff1 = self.comp.diff_vacant_rooms(vacant)
        self.assertListEqual(json.loads(diff1),
                             vacant)

        vacant1 = [[{'1': ['101', '102'],
                     '2': ['201']}, {}, {}, {}, {}], [], [], [], [], []]
        diff2 = self.comp.diff_vacant_rooms(vacant1)
        self.assertListEqual(json.loads(diff2),
                             [[{'1': None, '2': ['201']}, {}, {}, {}, {}],
                              [], [], [], [], []])

    def test_changes(self):
        self.storage['changes'] = 'null'

        chgs = [{'day': '1',
                 'wkday': 'monday',
                 'month': 'january',
                 '8А': ['some_changes']}]

        diff1 = self.comp.diff_changes(chgs)
        self.assertListEqual(json.loads(diff1),
                             chgs)

        chgs1 = [{'day': '1',
                  'wkday': 'monday',
                  'month': 'january',
                  '8А': ['some_changes'],
                  '9Б': ['more_changes']},
                 {'day': '2',
                  'month': 'january',
                  '10В': []}]

        diff2 = self.comp.diff_changes(chgs1)
        self.assertListEqual(json.loads(diff2),
                             [{'day': '1',
                               'wkday': 'monday',
                               'month': 'january',
                               '8А': None,
                               '9Б': ['more_changes']},
                              {'day': '2',
                               'month': 'january',
                               '10В': []}])

    def test_class_teachers(self):
        self.storage['class_teachers'] = 'null'

        tchrs = {'8А': [{}, {}]}

        diff1 = self.comp.diff_class_teachers(tchrs)
        self.assertDictEqual(json.loads(diff1),
                             tchrs)

        tchrs['9Б'] = []
        diff2 = self.comp.diff_class_teachers(tchrs)
        self.assertDictEqual(json.loads(diff2),
                             tchrs)
