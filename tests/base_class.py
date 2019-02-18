import time
import shutil
import unittest
from os import makedirs
from os.path import exists
from src.app import run_app
from multiprocessing import Process
from os.path import dirname, join, abspath

service_host = "127.0.0.1"
service_port = 8998
base_url = f"http://{service_host}:{service_port}"


class TestAdrestiaPdvBaseClass(unittest.TestCase):
    """
        Steps:
            1. Start the process service for each test.
            2. Ensure the process service is running.
            3. Terminate the process service for each test.
    """

    def setUp(self):
        """
            1. Start service as a forked process.
            2. Capture PID

        :return:
        """

        def bootstrap_service(host, port, results_directory):
            run_app(host, port, results_directory)

        self.results_dir = join(
            dirname(
                dirname(
                    abspath(__file__)
                )
            ),
            "test_data",
            str(int(time.time() * 10000))
        )
        makedirs(self.results_dir)
        p = Process(
            target=bootstrap_service,
            name='adrestia_pdv_tests',
            kwargs={
                "host": service_host,
                "port": service_port,
                "results_directory": self.results_dir
            }
        )
        p.start()
        self.service_process = p
        time.sleep(1)

    def tearDown(self):
        """
            1. terminate service process if alive
            2. cleanup the test data directory.
        :return:
        """
        if self.service_process.is_alive():
            self.service_process.terminate()
        for i in range(0, 100):
            if self.service_process.is_alive():
                time.sleep(1)
            else:
                break
        assert not self.service_process.is_alive(), \
            "tearDown expected to stop the service_process"
        shutil.rmtree(self.results_dir)
        assert not exists(self.results_dir)

    def test_adrestia_test_service_is_running(self):
        """
            Run the test step functions.
            :return:
        """
        assert self.service_process.is_alive(), \
            "Expected service process to be alive"
