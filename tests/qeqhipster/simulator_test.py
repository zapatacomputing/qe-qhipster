import pytest
from zquantum.core.interfaces.backend_test import (
    QuantumSimulatorTests,
    QuantumSimulatorGatesTest,
)

from qeqhipster.simulator import QHipsterSimulator
from qeqhipster.utils import make_circuit_qhipster_compatible


@pytest.fixture
def backend():
    return QHipsterSimulator()


@pytest.fixture()
def wf_simulator():
    return QHipsterSimulator()


class TestQHipster(QuantumSimulatorTests):
    pass


class TestQHipsterGates(QuantumSimulatorGatesTest):
    gates_to_exclude = ["XX", "YY", "ZZ", "XY", "ISWAP"]
    pass
