import pytest
from zquantum.core.interfaces.backend_test import (
    QuantumSimulatorTests,
    QuantumSimulatorGatesTest,
)
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
    pass


class TestQHipsterGates(QuantumSimulatorGatesTest):
    pass