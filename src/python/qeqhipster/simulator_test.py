import pytest
from zquantum.core.interfaces.backend_test import QuantumSimulatorTests
from .simulator import QHipsterSimulator


@pytest.fixture(
    params=[
        {},
        {"n_samples": 1000},
    ]
)
def backend(request):
    return QHipsterSimulator(**request.param)


@pytest.fixture(
    params=[
        {},
    ]
)
def wf_simulator(request):
    return QHipsterSimulator(**request.param)


class TestQHipster(QuantumSimulatorTests):
    def setUp(self):
        self.wf_simulators = [QHipsterSimulator()]
        self.backends = [QHipsterSimulator(n_samples=1000), QHipsterSimulator()]
