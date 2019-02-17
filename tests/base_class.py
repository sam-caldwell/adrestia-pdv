import time
import unittest
from src.app import run_app
from multiprocessing import Process

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

        def service_bootstrap(host: str, port: int):
            run_app(svc_host=host, svc_port=port)

        p = Process(
            target=service_bootstrap,
            name='adrestia_pdv_tests',
            kwargs={"host": service_host, "port": service_port}
        )
        p.start()
        self.service_process = p
        time.sleep(1)

    def tearDown(self):
        """
            1. terminate service process if alive

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

    def test_adrestia_test_service_is_running(self):
        """
            Run the test step functions.
            :return:
        """
        assert self.service_process.is_alive(), \
            "Expected service process to be alive"
