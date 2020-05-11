import unittest
import numpy as np
from zquantum.core.circuit import Circuit
from zquantum.core.bitstring_distribution import BitstringDistribution
from openfermion.ops import QubitOperator, IsingOperator
from .simulator import QHipsterSimulator
from pyquil import Program
from pyquil.gates import H, CNOT, RX, CZ, X

class TestQHipster(unittest.TestCase):

    def setUp(self):
        self.wf_simulator = QHipsterSimulator()
        self.sampling_simulator = QHipsterSimulator(n_samples=1000)
        self.all_simulators = [self.wf_simulator, self.sampling_simulator]

    def test_get_exact_expectation_values(self):
        # Given
        circuit = Circuit(Program(H(0), CNOT(0,1), CNOT(1,2)))
        qubit_operator = QubitOperator('[] + [Z0 Z1] + [X0 X2] ')
        # When
        expectation_values = self.wf_simulator.get_exact_expectation_values(circuit, qubit_operator)
        # Then
        self.assertAlmostEqual(sum(expectation_values.values), 2.0)

    def test_get_expectation_values(self):
        # Given
        circuit = Circuit(Program(H(0), CNOT(0,1), CNOT(1,2)))
        qubit_operator = IsingOperator('[] + [Z0 Z1] + [Z0 Z2] ')
        target_expectation_values = np.array([1., 1., 1.])
        # When
        expectation_values = self.sampling_simulator.get_expectation_values(circuit, qubit_operator)
        # Then
        np.testing.assert_array_almost_equal(expectation_values.values, target_expectation_values)

    def test_get_exact_expectation_values_empty_op(self):
        # Given
        circuit = Circuit(Program(H(0), CNOT(0,1), CNOT(1,2)))
        qubit_operator = QubitOperator()
        # When
        expectation_values = self.wf_simulator.get_exact_expectation_values(circuit, qubit_operator)
        # Then
        self.assertAlmostEqual(sum(expectation_values.values), 0.0)

    def test_run_circuit_and_measure(self):
        simulator = self.sampling_simulator
        # Given
        circuit = Circuit(Program(H(0), CNOT(0,1), CNOT(1,2)))
        # When
        simulator.n_samples = 100
        measurements = simulator.run_circuit_and_measure(circuit)
        # Then
        self.assertEqual(len(measurements.bitstrings), 100)
        self.assertEqual(len(measurements.bitstrings[0]), 3)

    def test_get_bitstring_distribution(self):
        for simulator in self.all_simulators:
            # Given
            circuit = Circuit(Program(H(0), CNOT(0,1), CNOT(1,2)))
            # When
            bitstring_distribution = simulator.get_bitstring_distribution(circuit)
            # Then
            self.assertEqual(type(bitstring_distribution), BitstringDistribution)
            self.assertEqual(bitstring_distribution.get_qubits_number(), 3)
            self.assertGreater(bitstring_distribution.distribution_dict["000"], 1/3)
            self.assertGreater(bitstring_distribution.distribution_dict["111"], 1/3)

    def test_run_circuit_and_measure_correct_bitstring_ordering(self):
        for simulator in self.all_simulators:
            # Given
            circuit = Circuit(Program(X(0), X(1), X(1), X(2), X(2)))
            # When
            simulator.n_samples = 1
            measurements = simulator.run_circuit_and_measure(circuit)
            # Then
            self.assertEqual(measurements.bitstrings, [(1,0,0)])



