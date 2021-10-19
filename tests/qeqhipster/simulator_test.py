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
    @pytest.mark.xfail
    def test_get_wavefunction_uses_provided_initial_state(self, wf_simulator):
        super().test_get_wavefunction_uses_provided_initial_state(wf_simulator)


class TestQHipsterGates(QuantumSimulatorGatesTest):
    gates_to_exclude = ["XX", "YY", "ZZ", "XY", "ISWAP"]
    pass
