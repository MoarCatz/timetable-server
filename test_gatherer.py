import unittest
from urllib.parse import urlencode, quote_plus
import json
from httmock import HTTMock, urlmatch
from gatherer import DataGatherer


@urlmatch(query='f=4')
def mock_class_list(url, req):
    return '\n'.join(['8а', '9Б', '10Я', '11о', '10П'])

@urlmatch(path='/study/calgraf.odt')
def mock_study_plan(url, req):
    with open('test_files/study_plan.odt', 'rb') as f:
        return f.read()

@urlmatch(path='/study', query='id=0')
def mock_rings_timetable(url, req):
    with open('test_files/rings_timetable.html') as f:
        return f.read()

@urlmatch(query='.*f=1.*')
def mock_perm_timetable(url, req):
    if quote_plus('8а', encoding='cp1251') not in url.query:
        return 'Class does not exist'

    with open('test_files/perm_timetable.json') as f:
        return f.read()

@urlmatch(query='.*f=2.*')
def mock_teacher_timetable1(url, req):
    if quote_plus('Сотрудник И. С.', encoding='cp1251') not in url.query:
        return 'Teacher does not exist or has no lessons'

    with open('test_files/teacher_timetable1.json') as f:
        return f.read()

@urlmatch(path='/study/izmenHtml.php')
def mock_changes(url, req):
    with open('test_files/changes.html') as f:
        return f.read()

@urlmatch(query='f=7')
def mock_teacher_list(url, req):
    return 'Учитель По Математике\nУчитель-Преподаватель По Экономике'

@urlmatch(query='.*f=2.*')
def mock_teacher_timetable2(url, req):
    if quote_plus('Учитель П. М.', encoding='cp1251') in url.query:
        with open('test_files/teacher_timetable2.json') as f:
            return f.read()

    with open('test_files/teacher_timetable3.json') as f:
        return f.read()

@urlmatch(path='/offic/', query='id=6')
def mock_teacher_data(url, req):
    single = urlencode({'famStaff': 'Учитель'}, encoding='cp1251')
    double = urlencode({'famStaff': 'Учитель-Преподаватель'},
                       encoding='cp1251')
    if double in req.body:
        with open('test_files/double_teacher_data.html') as f:
            return f.read()
    elif single in req.body:
        with open('test_files/single_teacher_data.html') as f:
            return f.read()
    return ''

@urlmatch(query='f=6')
def mock_all_rooms(url, req):
    return '\n'.join(['101', '102', '103',
                      '201', '202', '203',
                      '301', '302', '303'])

@urlmatch(query='.*f=3.*')
def mock_room_occupation(url, req):
    with open('test_files/room_occupation.json') as f:
        return f.read()

class TestDataGatherer(unittest.TestCase):
    def test_class_list(self):
        gth = DataGatherer()
        act_classes = ['8А', '9Б', '10Я', '11О', '10П']
        act_classes_grouped = {'8': ['8А'],
                               '9': ['9Б'],
                               '10': ['10Я', '10П'],
                               '11': ['11О']}

        with HTTMock(mock_class_list):
            self.assertListEqual(act_classes,
                                 gth.get_class_list(group=False))
            self.assertDictEqual(act_classes_grouped,
                                 gth.get_class_list())

    def test_study_plan(self):
        gth = DataGatherer()

        # December is the most eventful month, according to the 2017-18 data
        with open('test_files/december.json') as dec:
            act_december = json.load(dec)

        with HTTMock(mock_study_plan):
            self.assertListEqual(act_december,
                                 gth.get_study_plan()[3])

    def test_rings_timetable(self):
        gth = DataGatherer()
        act_rings = [{'start': '9:00', 'end': '9:40', 'type': 'lesson'},
                     {'len': 10, 'type': 'break'},
                     {'start': '9:50', 'end': '10:30', 'type': 'lesson'},
                     {'len': 15, 'type': 'break'},
                     {'start': '10:45', 'end': '11:25', 'type': 'lesson'},
                     {'len': 15, 'type': 'break'},
                     {'start': '11:40', 'end': '12:20', 'type': 'lesson'},
                     {'len': 15, 'type': 'break'},
                     {'start': '12:35', 'end': '13:15', 'type': 'lesson'},
                     {'len': 20, 'type': 'break'},
                     {'start': '13:35', 'end': '14:15', 'type': 'lesson'},
                     {'len': 20, 'type': 'break'},
                     {'start': '14:35', 'end': '15:15', 'type': 'lesson'}]

        with HTTMock(mock_rings_timetable):
            self.assertListEqual(act_rings,
                                 gth.get_rings_timetable())

    def test_perm_timetable(self):
        gth = DataGatherer()
        with open('test_files/act_perm_timetable.json') as f:
            act_timetable = json.load(f)

        with HTTMock(mock_perm_timetable):
            self.assertListEqual(act_timetable,
                                 gth.get_perm_timetable('8а'))
            self.assertIsNone(gth.get_perm_timetable('8б'))

    def test_full_perm_timetable(self):
        gth = DataGatherer()
        with open('test_files/act_perm_timetable.json') as f:
            act_timetable = json.load(f)

        pass_cls = '8А'
        with HTTMock(mock_class_list, mock_perm_timetable):
            full_tmtbl = gth.get_full_perm_timetable()

        for cls in full_tmtbl:
            if cls == pass_cls:
                self.assertListEqual(act_timetable,
                                     full_tmtbl[cls])
            else:
                self.assertIsNone(full_tmtbl[cls])

        self.assertSetEqual({'8А', '9Б', '10Я', '11О', '10П'},
                            set(full_tmtbl))

    def test_teacher_timetable(self):
        gth = DataGatherer()
        with open('test_files/act_teacher_timetable.json') as f:
            act_timetable = json.load(f)
        act_classes = ['8А', '9Б', '10В']

        with HTTMock(mock_teacher_timetable1):
            timetable, classes = gth.get_teacher_timetable('Сотрудник И. С.')
            timetable1, classes1 = gth.get_teacher_timetable('Нет Т. У.')
        self.assertListEqual(act_timetable,
                             timetable)
        self.assertSetEqual(set(act_classes),
                            set(classes))
        self.assertIsNone(timetable1)
        self.assertIsNone(classes1)

    def test_teachers(self):
        gth = DataGatherer()
        with open('test_files/act_teachers.json') as f:
            act_teachers = json.load(f)

        with HTTMock(mock_teacher_list,
                     mock_teacher_timetable2,
                     mock_teacher_data):
            teachers = gth.get_teachers()
            for teacher in teachers:
                for i in act_teachers:
                    if teacher['full'] == i['full']:
                        act_tchr = i
                        break

                self.assertCountEqual(act_tchr.pop('classes'),
                                      teacher.pop('classes'))
                self.assertDictEqual(act_tchr,
                                     teacher)

    def test_changes(self):
        gth = DataGatherer()
        with open('test_files/act_changes.json') as f:
            act_changes = json.load(f)

        with HTTMock(mock_changes):
            self.assertListEqual(act_changes,
                                 gth.get_changes())

    def test_vacant_rooms(self):
        gth = DataGatherer()
        with open('test_files/act_vacant_rooms.json') as f:
            act_vacant_rooms = json.load(f)

        with HTTMock(mock_all_rooms, mock_room_occupation):
            vacant_rooms = gth.get_vacant_rooms(wkday=6)
            for vacant, act_vacant in zip(vacant_rooms,
                                          act_vacant_rooms):
                for key in vacant:
                    self.assertCountEqual(vacant[key],
                                          act_vacant[key])

                self.assertCountEqual(vacant.keys(), act_vacant.keys())

    def test_class_teachers(self):
        gth = DataGatherer()
        act_class_teachers = {'8А': [{'teacher': 'Учитель П. И.',
                                      'subject': 'История'},
                                     {'teacher': 'Учитель П. М.',
                                      'subject': 'Математика'},
                                     {'teacher': 'Учитель П. Х.',
                                      'subject': 'Химия'},
                                     {'teacher': 'Учитель П. Ф.',
                                      'subject': 'Физика'},
                                     {'teacher': 'Учитель П. Л.',
                                      'subject': 'Литература'}]}

        with HTTMock(mock_class_list, mock_perm_timetable):
            class_teachers = gth.get_class_teachers()
            for cls in class_teachers:
                self.assertCountEqual(class_teachers[cls],
                                      act_class_teachers[cls])

unittest.main()
