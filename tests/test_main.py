import time
import requests
from os.path import join
from os.path import exists
from datetime import datetime
from src.app import get_version
from src.app import setup_results_dir
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
            assert exists(setup_results_dir()), "missing results directory"

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
        n = str(int(time.time()*10000))
        test_file = join(setup_results_dir(), f"test-{n}.results")
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

    def test_route_submit(self):
        """
            Test that we can submit reports and the files are written as
            expected.
            :return:
        """