import json
from glob import glob
from time import time
from os import getenv
from os import remove
from flask import Flask
from os import makedirs
from os.path import join, dirname, exists
from werkzeug.exceptions import BadRequest

app = Flask(__name__)


def setup_results_dir(results_directory) -> str:
    print("starting setup_results_dir()")
    if exists(results_directory):
        print(f"results_dir exists: '{results_directory}'")
    else:
        print("creating results directory")
        makedirs(results_directory)
    print("exiting setup_results_dir()")
    return results_directory


def get_version() -> str:
    with open(join(dirname(dirname(__file__)), 'VERSION.txt'), 'r') as f:
        return f.read().strip().lower()


def validate_file_name(name: str) -> bool:
    try:
        name.index(":")
        return False
    except ValueError:
        return True


def get_file_name(name: str) -> str:
    if validate_file_name(name):
        return join(app.config["results_dir"], f"{name}.results")
    else:
        raise ValueError(f"Bad PDV result name value {name}")


def validate_pdv_result(r: str):
    return r in ["pass", "fail"]


@app.route("/")
def route_home():
    return f"PDV Service (version: {get_version()})\n", 200


@app.route('/healthcheck')
def route_healthcheck():
    return "OK", 200


@app.route('/clear', methods=['DELETE'])
def route_clear():
    count = 0
    for file_name in glob(join(app.config["results_dir"], '*.results')):
        remove(join(app.config["results_dir"], file_name))
        count += 1

    return f"OK (Cleared {count} state files)", 200


@app.route('/submit/<name>/<result>', methods=['GET'])
def route_submit(name: str, result: str):
    data = {}
    try:
        data = {
            "name": name,
            "result": result,
            "time": time()
        }
        assert validate_pdv_result(result), "Expect only 'pass' or 'fail'."
        with open(get_file_name(name), 'w') as f:
            f.write(json.dumps(data, indent=2))
        return "OK", 200

    except AssertionError as e:
        data["error"] = "pdv_internal_error"
        with open(get_file_name('pdv_internal_error'), 'w') as f:
            f.write(json.dumps(data, indent=2))
        raise BadRequest(f"Invalid Input: {e}")


@app.route('/report', methods=["GET"])
def route_query():
    count = 0
    for file_name in glob(join(app.config["results_dir"], '*.results')):
        if file_name in [".", ".."]:
            continue
        else:
            print(f"sampling from {file_name}")
            with open(join(app.config["results_dir"], file_name)) as f:
                result_data = json.loads(f.read())
                count += 1
                if result_data["result"].strip().lower() == "fail":
                    result_data["error"] = None
                    result_data["count"] = count
                    return json.dumps(result_data)
                elif result_data["result"].strip().lower() == "pass":
                    continue
                else:
                    result_data["error"] = "Invalid result. Expect (pass|fail)"
                    result_data["count"] = count
                    return json.dumps(result_data), 500
    return json.dumps({
        "count": count,
        "error": None,
        "result": "pass"
    }), 200


def run_app(svc_host: str, svc_port: int, results_directory="data"):
    print("run_app() starting")
    app.config.update(
        results_dir=setup_results_dir(results_directory)
    )
    print("run_app() configured")
    app.run(host=svc_host, port=svc_port)


if __name__ == "__main__":
    print("starting...")
    host = getenv("ADRESTIA_PDV_SVC_HOST", "127.0.0.1")
    port = int(getenv("ADRESTIA_PDV_SVC_PORT", "8999"))
    results_dir = getenv("ADRESTIA_PDV_DATADIR", "/tmp")
    run_app(svc_host=host, svc_port=port, results_directory=results_dir)
