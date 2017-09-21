from typing import Tuple
from urllib.parse import urlencode, quote_plus
import json
import os
import re
import odf.opendocument
import odf.table
import odf.style
import requests


class Day:
    '''Represents a day in the calendar'''

    def __init__(self, day_num: int,
                       is_wknd: bool = False,
                       day_type: str = None):
        '''Initializes self. Requires the day number.
        Optional parameters include marking the day as a weekend and
        specifying the cell type'''
        self.day_num = day_num
        self.padding = None

        self.is_wknd = is_wknd
        self.day_type = day_type


class Calendar:
    '''Calendar object. Contains Day objects ordered by month'''

    def __init__(self):
        self.months = {}

    def add_month(self, month: str):
        '''Adds a given month to the calendar, initializing it with a list of
        32 elements. The first element represents the padding, the rest is for
        the days'''
        self.months[month] = [None] * 32

    def set_day(self, month: str, day_num: int, day: Day):
        '''Sets a day object for a given month'''
        if self.months[month][day_num] is not None:
            raise ValueError('day already exists')

        self.months[month][day_num] = day

    def set_padding(self, month: str, pad: int):
        '''Sets the month's padding. Padding is the amount of days from Monday
        until the start of the month'''
        self.months[month][0] = pad


class DataEncoder(json.JSONEncoder):
    '''Subclass to serialize Calendar objects to JSON. Also eliminates
    whitespace in the resulting JSON'''

    months_order = ['Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
                    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь']

    def __init__(self, **kwargs):
        kwargs['separators'] = (',', ':')
        super().__init__(**kwargs)

    def default(self, o):
        if not isinstance(o, Calendar):
            return super().default(o)

        cld = []
        for month in self.months_order:
            month_arr = [None] * o.months[month][0]
            for day in o.months[month][1:]:
                if day is None:
                    break
                day_obj = {'type': day.day_type,
                           'num': day.day_num}
                if day.is_wknd:
                    day_obj['wknd'] = True

                month_arr.append(day_obj)

            cld.append(month_arr)

        return cld


class ODTParser:
    '''Parser for the ODT table'''

    # TableCell nodes
    style_key = ('urn:oasis:names:tc:opendocument:xmlns:table:1.0',
                 'style-name')
    span_key = ('urn:oasis:names:tc:opendocument:xmlns:table:1.0',
                'number-columns-spanned')
    # Style nodes
    style_name_key = ('urn:oasis:names:tc:opendocument:xmlns:style:1.0',
                      'name')
    style_family_key = ('urn:oasis:names:tc:opendocument:xmlns:style:1.0',
                        'family')
    color_key = ('urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
                 'background-color')
    text_key = ('urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
                'color')
    # Text nodes
    text_style_key = ('urn:oasis:names:tc:opendocument:xmlns:text:1.0',
                      'style-name')

    def __init__(self, filename: str):
        '''Initializes self. Requires the filename of an ODT file'''
        self.doc = odf.opendocument.load(filename)

        content = self.doc.body.firstChild.childNodes
        self.table = content[1]
        self.legend = content[3]
        self.styles = self.doc.automaticstyles

        self.cell_types = {'учебные дни': 'study',
                           'сессия': 'session',
                           'каникулы': 'holidays'}

        self.style_to_cell = {}
        self.weekends = set()

    def collect_styles(self):
        '''Collects a mapping of a style name to a cell type
        (study, session, holidays). There's more than one style for each
        cell type, so this method collects them all.
        Also collects paragraph styles for weekends.

        Steps:
          1. Get the mapping of one of the styles to a cell type
             (taken from the table legend)
          2. Convert the styles to colors and get the mapping of color to
             cell type
          3. Go through styles and map their names to cell types by color
          4. Collect styles that represent weekends'''

        st_key = self.style_name_key
        # Step 1
        sample_styles = {}
        children = self.legend.getElementsByType(odf.table.TableCell)
        for i in range(1, len(children), 2):
            c_type = self.cell_types[str(children[i]).lower()]
            sample_styles[children[i - 1].attributes[self.style_key]] = c_type

        # Step 2
        color_to_cell = {}
        for obj in self.styles.getElementsByType(odf.style.Style):
            if obj.attributes[self.style_family_key] != 'table-cell':
                continue
            name = obj.attributes[st_key]
            if name in sample_styles:
                color = obj.childNodes[0].attributes[self.color_key]
                color_to_cell[color] = sample_styles[name]

        # Step 3
        for obj in self.styles.getElementsByType(odf.style.Style):
            if obj.attributes[self.style_family_key] != 'table-cell':
                continue
            name = obj.attributes[st_key]
            try:
                color = obj.childNodes[0].attributes[self.color_key]
                self.style_to_cell[name] = color_to_cell[color]
            except KeyError:
                continue

        # Step 4
        for obj in self.styles.getElementsByType(odf.style.TextProperties):
            if self.text_key in obj.attributes:
                self.weekends.add(obj.parentNode.attributes[st_key])

    def parse(self) -> Calendar:
        '''Iterates over the table and collects the cells' data'''
        self.collect_styles()

        rows = self.table.getElementsByType(odf.table.TableRow)
        clnd = Calendar()
        for i in range(1, len(rows), 8):
            # Iterate over month sections (section = header + 7 rows)
            headers = rows[i - 1].getElementsByType(odf.table.TableCell)[1:]
            header_widths = []

            for hdr in headers:
                month = str(hdr)
                width = int(hdr.attributes[self.span_key])
                header_widths.append((month, width))
                clnd.add_month(month)

            for j in range(i, i + 7):
                # Iterate over the 7 rows in the section
                days = rows[j].getElementsByType(odf.table.TableCell)[1:]
                curr_header_idx = 0
                curr_month, max_cells = header_widths[curr_header_idx]
                curr_cells = 0

                for k in days:
                    # Iterate over the day cells in each row
                    if curr_cells == max_cells:
                        curr_header_idx += 1
                        curr_month, max_cells = header_widths[curr_header_idx]
                        curr_cells = 0

                    curr_cells += 1
                    day, obj = self.cell_to_day(k)
                    if not day:
                        continue

                    if day == 1:
                        clnd.set_padding(curr_month, j - i)
                    clnd.set_day(curr_month, day, obj)

        return clnd

    def cell_to_day(self, cell: odf.table.TableCell) -> Tuple[int, Day]:
        '''Extracts the data from a table cell and constructs a Day object'''
        day = str(cell)
        if not day:
            return False, None

        day_num = int(day)

        text_key = self.text_style_key
        style = cell.attributes[self.style_key]
        is_wknd = cell.childNodes[0].attributes[text_key] in self.weekends
        try:
            cell_type = self.style_to_cell[style]
        except KeyError:
            cell_type = None

        obj = Day(day_num, is_wknd=is_wknd, day_type=cell_type)
        return day_num, obj


class DataGatherer:
    '''Class to collect data that is relevant to the application.
    Returns data in JSON'''

    def __init__(self):
        self.json = DataEncoder(ensure_ascii=False)

    def api_url(self, **kwargs) -> str:
        '''Returns a properly formed and encoded URL for the SESC API'''
        api_base = 'http://lyceum.urfu.ru/study/mobile.php?'
        return api_base + urlencode(kwargs, encoding='cp1251')


    def get_class_list(self, return_json=True) -> str:
        '''Gets the list of classes grouped by form
        If `json` is False, returns a list of classes without grouping'''

        url = self.api_url(f=4)
        resp = requests.get(url)
        if resp.status_code != 200:
            return None

        cls_list = resp.text.upper().splitlines()

        if not return_json:
            return cls_list

        classes = {'8': [],
                   '9': [],
                   '10': [],
                   '11': []}

        for i in cls_list:
            classes[i[:-1]].append(i)

        return self.json.encode(classes)

    def get_study_plan(self) -> str:
        '''Gets the study plan'''
        url = 'http://lyceum.urfu.ru/study/calgraf.odt'
        filename = 'calgraf.odt'
        resp = requests.get(url)
        if resp.status_code != 200:
            return None

        with open(filename, 'wb') as file:
            file.write(resp.content)

        plan = ODTParser(filename).parse()

        os.remove(filename)

        return self.json.encode(plan)

    def get_rings_timetable(self) -> str:
        '''Gets the rings timetable and computes the breaks' length'''
        ptn = re.compile('<td>[1-7] урок</td>' +
                         '(?:<td>(?:&nbsp;)?([0-9]{1,2}):([0-9]{2})</td>)' * 2)

        url = 'http://lyceum.urfu.ru/study/?id=0'
        resp = requests.get(url)
        if resp.status_code != 200:
            return None

        lessons = ptn.findall(resp.text)
        table = []
        for idx, elem in enumerate(lessons):
            sh, sm, eh, em = elem
            table.append({'type': 'lesson',
                          'start': sh + ':' + sm,
                          'end': eh + ':' + em})
            try:
                break_len = int(lessons[idx + 1][1]) - int(em)
                if break_len < 0:
                    break_len += 60
                table.append({'type': 'break',
                              'len': break_len})
            except IndexError:
                pass

        return self.json.encode(table)

    def get_perm_timetable(self, cls: str) -> list:
        '''Returns the permanent timetable for a given class as a list'''
        timetable = [[] for i in range(6)]

        url = self.api_url(f=1, k=cls.lower())
        resp = requests.get(url)
        if resp.status_code != 200:
            return None

        week = json.loads(resp.text)[cls.lower()]['Timetable']

        for idx, day in enumerate(week):
            lessons = day['Lessons']
            for lesson in lessons:
                form_lsns = []
                for group in lesson['LessonsByGroups']:
                    form_lsns.append({'name': group['Subject'],
                                      'teacher': group['Teacher'],
                                      'room': group['Classroom']})

                timetable[idx].append(form_lsns)

        return timetable

    def get_full_perm_timetable(self):
        '''Returns the permanent timetable for all classes'''
        cls_list = self.get_class_list(return_json=False)

        full_tmtb = {cls: self.get_perm_timetable(cls) for cls in cls_list}

        return self.json.encode(full_tmtb)

    def get_teacher_timetable(self, abbr_name: str) -> Tuple[list, list]:
        '''Returns a timetable for a given teacher's abbreviated name and
        a list of classes that have lessons with this teacher'''
        week_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг',
                     'Пятница', 'Суббота']
        url = self.api_url(f=2, p=abbr_name)
        resp = requests.get(url)
        if resp.status_code != 200:
            return None

        try:
            week = json.loads(resp.text)[abbr_name]['Timetable']
        except json.decoder.JSONDecodeError:
            return None, None

        timetable = [None] * 6
        classes = set()
        for day in week:
            day_number = week_days.index(day['Day'])
            lessons = [None] * 7
            for lsn in day['Lessons']:
                lsn_obj = {}
                lsn_number = int(lsn['Number']) - 1
                cls = lsn['Class'].upper()
                classes.add(cls)

                lsn_obj['class'] = cls
                lsn_obj['room'] = lsn['Classroom']
                lsn_obj['name'] = lsn['Subject']

                lessons[lsn_number] = lsn_obj

            timetable[day_number] = lessons

        return timetable, list(classes)

    def get_teachers(self) -> str:
        '''Returns full information about every teacher'''
        info_url = 'http://lyceum.urfu.ru/offic/?id=6'
        info_ptn = re.compile('<tr>'
                              '<td>([^<]+?)</td>'  # Full name
                              '<td>([^<]+?)</td>'  # Department
                              '<td>([^<]+?)</td>'  # Job
                              '<td class=\'c\'>')

        url = self.api_url(f=7)
        resp = requests.get(url)
        if resp.status_code != 200:
            return None

        tch_list = resp.text.splitlines()
        teachers = []
        for full_name in tch_list:
            tch_obj = {}
            tch_obj['full'] = full_name

            last, first, patr = full_name.split()
            abbr_name = last + ' {}. {}.'.format(first[0], patr[0])
            tch_obj['abbr'] = abbr_name

            # Collect job and department
            req_data = {'subStaff': '%C8%F1%EA%E0%F2%FC',
                        'unitStaff': '0',
                        'famStaff': quote_plus(last, encoding='cp1251')}
            data_str = '&'.join(k + '=' + v for k, v in req_data.items())
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            resp = requests.post(info_url,
                                 data=data_str,
                                 headers=headers)

            for match in info_ptn.findall(resp.text.replace('&nbsp;', ' ')):
                if full_name == match[0]:
                    tch_obj['dep'] = match[1]
                    tch_obj['job'] = match[2]
                    break

            # Collect timetable
            tmtbl, classes = self.get_teacher_timetable(abbr_name)
            if tmtbl is not None:
                tch_obj['timetable'] = tmtbl
                tch_obj['classes'] = classes

            teachers.append(tch_obj)

        return self.json.encode(teachers)
