from flask import Flask, render_template, request, jsonify
from ansible_plugins.exec_playbook import ExecPlaybook
from ansible_plugins.callback_mongo import ResultModel
from threading import Thread

app = Flask(__name__)
result = ResultModel()


def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()

    return wrapper


@async
def my_ansible(id):
    play = ExecPlaybook(['/home/sh01318/git/demo/ansible_plugins/test.yaml'], id)
    play.add_host('192.168.3.210')
    play.add_host(host='172.16.8.248', port=22, user='root', passwd='dskskdjf', private_file=None)
    play.add_playbook_vars('name', 'ceshi1')
    play.add_playbook_vars('name2', 'ceshi2')
    play.run()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logs')
def ansible_logs():
    id = request.args.get('id')
    doc = result.find_logs(track_id=id)
    if doc:
        return jsonify({"logs": doc['logs'], "status": doc['status']})
    else:
        return jsonify({"logs": "", "status": ""})


@app.route('/exec')
def exec_ansible():
    id = request.args.get('id')
    my_ansible(id)
    return 's'


if __name__ == '__main__':
    app.run()
