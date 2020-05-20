import unittest
from zquantum.core.interfaces.backend_test import QuantumSimulatorTests
from .simulator import QHipsterSimulator

class TestQHipster(unittest.TestCase, QuantumSimulatorTests):

    def setUp(self):
        self.wf_simulators = [QHipsterSimulator()]
        self.backends = [QHipsterSimulator(n_samples=1000), QHipsterSimulator()]



