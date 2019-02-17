import requests
from datetime import datetime
from src.app import get_version
from tests.base_class import base_url
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

    def test_version_format(self):
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
