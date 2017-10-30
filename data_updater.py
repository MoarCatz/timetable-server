import json
import logging
import os
import sys
from urllib.parse import urlparse

import requests

from diff_computer import DiffComputer, NoUpdate
from gatherer import DataGatherer
from storage import Storage


log_fmt = logging.Formatter('[{asctime}] [{levelname}] [{name}]\n{message}\n',
                            datefmt='%d-%m %H:%M:%S',
                            style='{')

cns_log = logging.StreamHandler()
cns_log.setLevel(logging.DEBUG)
cns_log.setFormatter(log_fmt)

class OneSignal:
    '''Class to communicate with the OneSignal API
    for sending push notifications'''

    headers = {'Content-Type': 'application/json',
               'Authorization': os.environ['ONESIGNAL_AUTH']}
    api_url = 'https://onesignal.com/api/v1/notifications'
    app_id = '928a41eb-7482-4dd3-b6e3-45fe9789fee1'
    error_msg = 'push notification rejected ({})'

    log = logging.Logger('OneSignal')
    log.addHandler(cns_log)
    log.setLevel(logging.DEBUG)

    @classmethod
    def send(cls, key: str, value: str):
        '''Sends a push notification that consists of a key and a value.
        The key is sent as the heading, the value is sent as the body'''
        payload = {'app_id': cls.app_id,
                   'included_segments': ['Active Users', 'Inactive Users'],
                   'headings': {'en': key},
                   'contents': {'en': value}}

        resp = requests.post(cls.api_url,
                             headers=cls.headers,
                             data=json.dumps(payload))

        if resp.status_code != 200:
            cls.log.error(cls.error_msg.format(resp.status_code))


class DataUpdater:
    '''Class to control the data updating and delivery'''
    url = urlparse(os.environ['DATABASE_URL'])
    store = Storage(host=url.hostname,
                    dbname=url.path[1:],
                    user=url.username,
                    password=url.password)
    gth = DataGatherer()
    comp = DiffComputer(store)

    log = logging.Logger('OneSignal')
    log.addHandler(cns_log)
    log.setLevel(logging.DEBUG)

    cmd_map = {'class_list': (gth.get_class_list,
                              comp.diff_class_list),
               'study_plan': (gth.get_study_plan,
                              comp.diff_study_plan),
               'rings_timetable': (gth.get_rings_timetable,
                                   comp.diff_rings_timetable),
               'full_perm_timetable': (gth.get_full_perm_timetable,
                                       comp.diff_full_perm_timetable),
               'teachers': (gth.get_teachers,
                            comp.diff_teachers),
               'changes': (gth.get_changes,
                           comp.diff_changes),
               'vacant_rooms': (gth.get_vacant_rooms,
                                comp.diff_vacant_rooms),
               'class_teachers': (gth.get_class_teachers,
                                  comp.diff_class_teachers)}
    @classmethod
    def get_cmd(cls) -> str:
        '''Retrieves a command from the program's arguments or
        prints a help message on failure'''
        if len(sys.argv) < 2 or sys.argv[1] not in cls.cmd_map:
            print('Usage: {} cmd'.format(sys.argv[0]))
            print('cmd can be one of the following:')
            for cmd in cls.cmd_map:
                print(' -', cmd)
            sys.exit(0)

        return sys.argv[1]

    @classmethod
    def update(cls):
        '''Activates the updating process'''
        cmd = cls.get_cmd()
        gather, diff = cls.cmd_map[cmd]
        try:
            result = diff(gather())
            cls.log.debug('computed diff for {}'.format(cmd))
            cls.log.debug(result)
            OneSignal.send(cmd, result)
        except NoUpdate:
            cls.log.info('no update needed')

DataUpdater.update()
