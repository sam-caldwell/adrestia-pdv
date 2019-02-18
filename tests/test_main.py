import time
import json
import requests
from glob import glob
from os.path import join
from os.path import exists
from datetime import datetime
from src.app import get_version
from tests.base_class import base_url
from src.app import validate_file_name
from tests.base_class import TestAdrestiaPdvBaseClass


class TestMain(TestAdrestiaPdvBaseClass):

    @staticmethod
    def check_methods(end_point: str, vectors: list):
        """
            Scan the given endpoint with a set of http methods and ensure
            only those allowed return 200 and all others return 405.

            :param end_point: http endpoint.
            :param vectors: expected behavior descriptor
            :return:
        """
        for http in vectors:
            func = http["method"]
            response = func(end_point)
            assert response.status_code == http["expected"], \
                f"failed on {func} status_code"
            if http["text"] is not None:
                assert response.text == http["text"], \
                    f"failed on {func} text"

    def test_core_functions(self):
        """
            Running a bunch of tests as steps inside a single test method
            to speed things up (avoiding setup and teardown)

            :return:
        """

        def step_version_format():
            """
                Test the format of the version string.
                :return:
            """
            v = get_version()
            assert v.strip() == v, "version contains strippable characters"
            assert v.lower() == v, "version contains non-lowercase characters"
            v_split = v.split('.')
            assert len(v_split) == 3, "version expects 3 dot-delimited ints"
            assert int(v_split[0]), "version expects <int>.xx.xx"
            assert int(v_split[1]), "version expects xxxx.<int>.xx"
            assert int(v_split[2]), "version expects xxxx.xx.<int>"

            now = datetime.now()
            current_year = now.year
            current_month = now.month
            current_day = now.day

            assert int(v_split[0]) == current_year
            assert int(v_split[1]) == current_month
            assert int(v_split[2]) == current_day

        def step_results_dir():
            assert exists(self.results_dir), "missing results directory"

        def step_validate_filename():
            assert validate_file_name(
                "test_happy"), "expected passing validation"
            assert not validate_file_name("test:happy"), "expected failure"

        #
        # run the steps...
        #
        step_version_format()
        step_results_dir()
        step_validate_filename()

    def test_route_healthcheck(self):
        """
            Test the healthcheck endpoint.
            :return:
        """
        endpoint = f"{base_url}/healthcheck"
        vectors = [
            {"method": requests.get, "expected": 200, "text": "OK"},
            {"method": requests.put, "expected": 405, "text": None},
            {"method": requests.post, "expected": 405, "text": None},
            {"method": requests.delete, "expected": 405, "text": None}
        ]
        self.check_methods(endpoint, vectors)

    def test_route_home(self):
        """
            Test the / route.
        :return:
        """

        endpoint = f"{base_url}/"
        vectors = [
            {"method": requests.get, "expected": 200,
             "text": f"PDV Service (version: {get_version()})\n"},
            {"method": requests.put, "expected": 405, "text": None},
            {"method": requests.post, "expected": 405, "text": None},
            {"method": requests.delete, "expected": 405, "text": None}
        ]
        self.check_methods(endpoint, vectors)

    def test_route_clear_method_scan(self):
        """
            Test the /clear route methods
        :return:
        """

        endpoint = f"{base_url}/clear"
        vectors = [
            {"method": requests.get, "expected": 405, "text": None},
            {"method": requests.put, "expected": 405, "text": None},
            {"method": requests.post, "expected": 405, "text": None},
            {"method": requests.delete, "expected": 200, "text": None}
        ]
        self.check_methods(endpoint, vectors)

    def test_route_clear(self):
        """
            Test that the /clear endpoint will actually do it's job
            and clear out files in the results_dir.
            :return:
        """
        endpoint = f"{base_url}/clear"
        n = str(int(time.time() * 10000))
        results_directory = self.results_dir
        test_file = join(results_directory, f"test-{n}.results")
        assert not exists(test_file), \
            "A Test data file already exists. " \
            "We failed to cleanup after ourselves.  " \
            "Mommy isn't here to do this for you and this ain't JAVA."

        test_data = str(time.time())
        with open(test_file, 'w') as f:
            f.write(test_data)
        assert exists(test_file), "Test data file not created."
        with open(test_file, 'r') as f:
            assert f.read() == test_data, "Test data mismatch on setup."
        #
        # setup is complete.  We have clearable data.
        #
        response = requests.delete(endpoint)
        assert response.status_code == 200, "Expected HTTP/200 response"
        assert response.text == f"OK (Cleared 1 state files)", \
            "response text mismatch."
        assert not exists(test_file), \
            "Expected test file to have been cleared"

    def test_route_submit_scan(self):
        """
            Test the /clear route methods
            :return:
        """

        endpoint = f"{base_url}/submit/test.route.submit.scan/pass"
        vectors = [
            {"method": requests.get, "expected": 200, "text": None},
            {"method": requests.put, "expected": 405, "text": None},
            {"method": requests.post, "expected": 405, "text": None},
            {"method": requests.delete, "expected": 405, "text": None}
        ]
        self.check_methods(endpoint, vectors)

    def validate_file_exists(self, test_name):
        """

            :param test_name:
            :return:
        """
        return exists(join(self.results_dir, f"{test_name}.results"))

    def test_route_submit(self):
        """
            Test that we can submit reports and the files are written as
            expected.
            :return:
        """
        test_name = "test.route.submit"
        endpoint = f"{base_url}/submit/{test_name}"
        for method in [requests.get]:
            test_results = [
                {"result": "pass", "expects": 200, "text": "OK"},
                {"result": "fail", "expects": 200, "text": None},
                {"result": "Pass", "expects": 400, "text": None},
                {"result": "Fail", "expects": 400, "text": None},
                {"result": "badResult", "expects": 400, "text": None}
            ]
            for data in test_results:
                result = data["result"]
                expectation = data["expects"]
                response = method(f"{endpoint}/{result}")
                assert response.status_code == expectation, \
                    f"Expected {expectation} on {method}"
                if data["text"] is not None:
                    assert response.text == "OK", \
                        f"Expected OK text on {method}"
                assert self.validate_file_exists(test_name), \
                    f"missing test result:{test_name}."

    def test_route_report(self):
        """
            Test that we can generate a PDV report from a set of files.
            :return:
        """

        def generate_tests(p: int, t_strategy: str, freq: int) -> (str, str):
            """
                This will generate tuples of tests and results (pass,fail)
                :return:
            """

            def choose_result(n: int) -> str:
                """
                    choose 1 / 5 as failed tests.  This will allow several
                    passes for every fail, since a single fail will stop
                    processing.
                    :param n:
                    :return:
                """
                if t_strategy == "pass":
                    return "pass"
                elif t_strategy == "fail":
                    return "fail"
                else:
                    return "fail" if n % freq == 0 else "pass"

            return f"test{p}", choose_result(p)

        def fuzzing_reports(count: int, test_strategy: str, mix_freq):
            """
                Given a count of tests to run (test<n>) and a strategy
                (e.g. all passes, all fails or a mix of a given frequency),
                submit the reports to the pdv service process then run a
                report and evalaute the outcome.

                :param count:
                :param test_strategy:
                :param mix_freq:
                :return:
            """
            for i in range(0, count):
                test_name, result = generate_tests(i, test_strategy, mix_freq)
                endpoint = f"{base_url}/submit/{test_name}/{result}"
                response = requests.get(endpoint)
                assert response.status_code == 200, "Expect 200 on submit"
                assert response.text == "OK", "Expect OK on submit"
            file_list = glob(join(self.results_dir, "*.results"))
            assert count == len(file_list), \
                "file count does not match test count"
            #
            # We know that our tests contain fails.
            # We expect a failed outcome.
            #
            endpoint = f"{base_url}/report"
            response = requests.get(endpoint)
            assert response.status_code == 200, "Expect 200 on /report"
            data = json.loads(response.text)
            assert "result" in data, \
                "Missing results attribute in response data."
            assert "count" in data, \
                "Missing count attribute in response data."
            assert "error" in data, \
                "Missing error attribute in response data."

            if data["result"] == "pass":
                assert strategy != "fail", \
                    "one fail would fail all, so we cannot have a " \
                    "passing result."
            else:
                assert strategy != "pass", \
                    "for a passing strategy we expect all passes."
                assert "name" in data, \
                    "Missing name attribute in response data."
                assert "time" in data, \
                    "Missing time attribute in response data."
                assert data["result"] == "fail", "Expected failure."
                assert str(data["time"]) == str(
                    float(data["time"])), "time is not float"
            if strategy == "pass":
                assert data["count"] == count
            elif strategy == "fail":
                assert data["count"] == 1
            else:
                assert data["count"] == mix_freq, \
                    "Expected to fail on first test."

        for strategy in ["pass", "fail", "mixed"]:
            fuzzing_reports(count=100, test_strategy=strategy, mix_freq=5)
