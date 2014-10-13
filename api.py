from flask import Flask, request
from rq import Queue

from worker import conn
from autobuild import autobuild

app = Flask(__name__)

q = Queue(connection=conn)

@app.route('/rebuild/<region>', methods=['POST'])
def run(region):
    regions = ['uk', 'world'] if region == 'all' else region
    repo = request.get_json()["repository"]["name"]
    for region in regions:
        # TODO: split the task up so we don't need to use this timeout hack
        q.enqueue_call(func=autobuild, args=(region, repo), timeout=1000)
    return 'Rebuild triggered.'

if __name__ == "__main__":
    app.run()
