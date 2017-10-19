import sys

from diff_computer import DiffComputer
from gatherer import DataGatherer

gth = DataGatherer()
comp = DiffComputer()

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

if len(sys.argv) < 2 or sys.argv[1] not in cmd_map:
    print('Usage: {} cmd'.format(sys.argv[0]))
    print('cmd can be one of the following:')
    for cmd in cmd_map:
        print(' -', cmd)
    sys.exit(0)

gather, diff = cmd_map[sys.argv[1]]
result = diff(gather())
print(result)

