from flask import Flask, request
from rq import Queue

from worker import conn
from autobuild import autobuild

app = Flask(__name__)

q = Queue(connection=conn)

@app.route('/rebuild/<region>', methods=['GET', 'POST'])
def run(region):
    reason = request.args.get('repo', None)
    # TODO: split the task up so we don't need to use this timeout hack
    q.enqueue_call(func=autobuild, args=(region, reason), timeout=1000)
    return 'Scheduled!'

if __name__ == "__main__":
    app.run()
