from os import mkdir
from os import getenv
from glob import glob
from time import time
from os import getenv
from os import remove
from flask import Flask
from os.path import abspath
from os.path import join, dirname, exists
from werkzeug.exceptions import BadRequest

app = Flask(__name__)

results_dir = getenv('RESULTS_DIRECTORY',
                     join(abspath(dirname(__file__)), 'data'))
if exists(results_dir):
    print(f"results_dir exists: '{results_dir}'")
else:
    print("creating results_dir")
    mkdir(results_dir)


def get_version():
    with open(join(dirname(dirname(__file__)), 'VERSION.txt'), 'r') as f:
        return f.read().strip().lower()


def get_file_name(name: str) -> str:
    try:
        name.index(":")
        raise Exception("An invalid name containing a ':' char passed to pdv.")
    except ValueError:
        pass
    return join(results_dir, f"{name}.results")


@app.route("/")
def route_home():
    return f"PDV Service (version: {get_version()})\n", 200


@app.route('/healthcheck')
def route_healthcheck():
    return "OK", 200


@app.route('/clear', methods=['DELETE'])
def route_reset_state():
    count = 0
    for file_name in glob(join(results_dir, '*.results')):
        remove(join(results_dir, file_name))
        count += 1

    return f"OK (Cleared {count} state files)", 200


@app.route('/submit/<name>/<result>', methods=['PUT', 'GET'])
def route_submit(name: str, result: str):
    try:
        invalid_result = -1
        valid_results = ["pass", "fail"]  # index of result is the code. ;-)
        i = valid_results.index(result)
        if i == invalid_result:
            raise BadRequest("Invalid results passed to pdv service")
        else:
            with open(get_file_name(name), 'w') as f:
                f.write(f"{name}:{i}:{time()}")
            return "OK", 200
    except Exception as e:
        with open(get_file_name('pdv_internal_error'), 'w') as f:
            f.write(f"pdv_internal_error:1:{time()}")
        raise BadRequest(e)


@app.route('/report/', methods=["GET"])
def route_query():
    count = 0
    for file_name in glob(join(results_dir, '*.results')):
        if file_name not in [".", ".."]:
            print(f"sampling from {file_name}")
            with open(join(results_dir, file_name)) as f:
                this_result = f.read().strip().lower().split(':')
                count += 1
                if this_result[1].strip().lower() == "fail":
                    return f"fail:" \
                           f"count={count}:" \
                           f"{this_result[1]}:" \
                           f"{this_result[2]}\n", 200
    return f"pass:count={count}\n", 200  # Pass


def run_app(svc_host: str, svc_port: int):
    app.run(host=svc_host, port=svc_port)


if __name__ == "__main__":
    host = getenv("ADRESTIA_PDV_SVC_HOST", "127.0.0.1")
    port = int(getenv("ADRESTIA_PDV_SVC_PORT", "8999"))
    run_app(svc_host=host, svc_port=port)
