import json
from encoder import NoWSEncoder
from storage import Storage


class NoUpdate(Exception):
    '''Exception to signify that no update is necessary'''


class DiffComputer:
    '''Computes differences between the old and newly fetched data.
    This is to reduce data transfer and not to update identical data.
    Diffing methods return the processed data in JSON'''

    def __init__(self, storage: Storage):
        self.storage = storage
        self.json = NoWSEncoder()

    def exchange(self, key: str, value):
        '''Exchanges the old data with the given key for a new value.
        Returns the old data piece, JSON-decoded.
        If the new value is equal to what already was in the storage or
        new data failed to get fetched, raises NoUpdate'''
        try:
            old = json.loads(self.storage[key])
            if old == value:
                raise NoUpdate
        except KeyError:
            old = None

        if value is None:
            raise NoUpdate
        self.storage[key] = self.json.encode(value)
        return old

    def diff_class_list(self, new: dict) -> str:
        old = self.exchange('class_list', new)
        if old is None:
            return self.json.encode(new)

        for form, classes in old.items():
            if form in new and classes == new[form]:
                new[form] = None

        return self.json.encode(new)

    def diff_study_plan(self, new: list) -> str:
        old = self.exchange('study_plan', new)
        if old is None:
            return self.json.encode(new)

        for m_idx, month in enumerate(old):
            if month == new[m_idx]:
                new[m_idx] = None

        return self.json.encode(new)

    def diff_rings_timetable(self, new: list) -> str:
        self.exchange('rings_timetable', new)
        return self.json.encode(new)

    @staticmethod
    def diff_timetable(old: list, new: list) -> list:
        for d_idx, day in enumerate(old):
            for l_idx, lesson in enumerate(day):
                if lesson == new[d_idx][l_idx]:
                    new[d_idx][l_idx] = None

        return new

    def diff_full_perm_timetable(self, new: dict) -> str:
        old = self.exchange('full_perm_timetable', new)
        if old is None:
            return self.json.encode(new)

        for cls, tmtbl in old.items():
            if cls in new:
                new[cls] = self.diff_timetable(tmtbl, new[cls])

        return self.json.encode(new)

    def diff_teachers(self, new: list) -> str:
        old = self.exchange('teachers', new)
        if old is None:
            return self.json.encode(new)

        name_lookup = {i['abbr']: i for i in new if 'abbr' in i}

        for teacher in old:
            try:
                new_tchr = name_lookup[teacher['abbr']]
            except KeyError:
                continue

            for field in ('full', 'dep', 'job', 'classes'):
                try:
                    if new_tchr[field] == teacher[field]:
                        new_tchr[field] = None
                except KeyError:
                    pass
            try:
                new_tchr['timetable'] = self.diff_timetable(
                    teacher['timetable'],
                    new_tchr['timetable'])
            except KeyError:
                pass

        return self.json.encode(new)

    def diff_vacant_rooms(self, new: list) -> str:
        old = self.exchange('vacant_rooms', new)
        if old is None:
            return self.json.encode(new)

        for day_idx, old_day in enumerate(old):
            for lsn_idx, lesson in enumerate(old_day):
                for floor, rooms in lesson.items():
                    if new[day_idx][lsn_idx][floor] == rooms:
                        new[day_idx][lsn_idx][floor] = None

        return self.json.encode(new)

    def diff_changes(self, new: list) -> str:
        old = self.exchange('changes', new)
        if old is None:
            return self.json.encode(new)

        day_lookup = {(i['day'], i['month']): i for i in new}

        reserved = {'day', 'month', 'wkday'}
        for day in old:
            new_day = day_lookup[(day['day'], day['month'])]
            for prop in day:
                if prop in reserved:
                    continue

                if day[prop] == new_day[prop]:
                    new_day[prop] = None

        return self.json.encode(new)

    def diff_class_teachers(self, new: dict) -> str:
        self.exchange('class_teachers', new)
        return self.json.encode(new)
