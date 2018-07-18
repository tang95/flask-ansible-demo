# coding: utf-8
from ansible.playbook.task_include import TaskInclude
from ansible.utils.color import colorize, hostcolor
from ansible import constants as C
from ansible.plugins.callback import default
from pymongo import MongoClient
from ansible.utils.display import Display

import errno
import sys
from ansible import constants as C
from ansible.module_utils._text import to_bytes, to_text
from ansible.utils.color import stringc

class ResultModel(object):

    def __init__(self):
        self.host = 'localhost'
        self.port = 27017
        self.database = 'devops'
        self.username = 'devops'
        self.password = 'devops'
        self.collection = 'ansible'
        self.client = MongoClient(
            'mongodb://%s:%s@%s:%s/%s' % (self.username, self.password, self.host, self.port, self.database))
        self.db = self.client[self.database]
        # self.db = self.client[self.database][self.collection].ensure_index('track_id', unique=True)

    def inster(self, data):
        self.db[self.collection].insert_one(data)

    def update(self, track_id, data, type="ansible"):
        if type == "ansible":
            doc = self.db[self.collection].find_one({'track_id': track_id})
            for k, v in data.items():
                doc[k] = v
            self.db[self.collection].update({'track_id': track_id}, {"$set": doc})
        if type == "logs":
            self.db[self.collection].update({'track_id': track_id}, {"$push": data})

    def find_logs(self, track_id):
        return self.db[self.collection].find_one({'track_id': track_id})


class MyDisplay(Display):

    def __init__(self, track_id, verbosity=0):
        super(MyDisplay, self).__init__(verbosity)
        self.track_id = track_id

    def display(self, msg, color=None, stderr=False, screen_only=False, log_only=False):
        """ Display a message to the user

        Note: msg *must* be a unicode string to prevent UnicodeError tracebacks.
        """
        if color:
            msg = stringc(msg, color)

        if not log_only:
            if not msg.endswith(u'\n'):
                msg2 = msg + u'\n'
            else:
                msg2 = msg

            msg2 = to_bytes(msg2, encoding=self._output_encoding(stderr=stderr))
            if sys.version_info >= (3,):
                # Convert back to text string on python3
                # We first convert to a byte string so that we get rid of
                # characters that are invalid in the user's locale
                msg2 = to_text(msg2, self._output_encoding(stderr=stderr), errors='replace')

            # Note: After Display() class is refactored need to update the log capture
            # code in 'bin/ansible-connection' (and other relevant places).
            if not stderr:
                fileobj = sys.stdout
            else:
                fileobj = sys.stderr

            fileobj.write(msg2)

            ResultModel().update(track_id=self.track_id, type="logs", data={"logs": msg2})
            try:
                fileobj.flush()
            except IOError as e:
                # Ignore EPIPE in case fileobj has been prematurely closed, eg.
                # when piping to "head -n1"
                if e.errno != errno.EPIPE:
                    raise



class ResultCallback(default.CallbackModule):

    def __init__(self, track_id):
        super(ResultCallback, self).__init__()
        self.track_id = track_id
        self.mongo = ResultModel()
        self._display = MyDisplay(track_id=track_id)

    def v2_playbook_on_stats(self, stats):
        self._display.banner("PLAY RECAP")
        state = []
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            self._display.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], C.COLOR_OK),
                colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                colorize(u'failed', t['failures'], C.COLOR_ERROR)),
                                  screen_only=True
                                  )
            state.append({
                u"host": h,
                u'ok': t['ok'],
                u'changed': t['changed'],
                u'unreachable': t['unreachable'],
                u'failed': t['failures']
            })
        if len(stats.failures) > 0:
            self.mongo.update(track_id=self.track_id, data={
                "state": state,
                "status": 'ok'
            })
        else:
            self.mongo.update(track_id=self.track_id, data={
                "state": state,
                "status": 'failed'
            })

    def v2_playbook_on_play_start(self, play):
        name = play.get_name().strip()
        if not name:
            msg = u"PLAY"
        else:
            msg = u"PLAY [%s]" % name

        self._play = play
        self.mongo.update(track_id=self.track_id, data={
            "playbook_name": name,
            "extra_vars": play._variable_manager.extra_vars,
            "status": "start"
        })
        self._display.banner(msg)
