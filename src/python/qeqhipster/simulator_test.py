import unittest
from zquantum.core.interfaces.backend_test import QuantumSimulatorTests
from .simulator import QHipsterSimulator
from pyquil.gates import X
from pyquil import Program
from openfermion import IsingOperator
from zquantum.core.circuit import Circuit
from zquantum.core.measurement import ExpectationValues
import numpy as np

class TestQHipster(unittest.TestCase, QuantumSimulatorTests):

    def setUp(self):
        self.wf_simulators = [QHipsterSimulator()]
        self.backends = [QHipsterSimulator(n_samples=1000), QHipsterSimulator()]

    def test_get_expectation_values_for_Z(self):
        # Given
        circuit = Circuit(Program(X(0)))
        operator = IsingOperator('3[Z0]')
        target_expectation_values = np.array([-3])
        n_samples = 1
        # When
        for backend in self.backends:
            backend.n_samples = 1
            expectation_values = backend.get_expectation_values(circuit, operator)
            # Then
            self.assertIsInstance(expectation_values, ExpectationValues)
            np.testing.assert_array_almost_equal(expectation_values.values, target_expectation_values, decimal=15)



