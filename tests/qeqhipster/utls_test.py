import numpy as np
import sympy
import pytest
from zquantum.core.wip import circuits
from qeqhipster.utils import make_circuit_qhipster_compatible


class TestMakingCircuitCompatibleWithQHipster:
    def test_circuit_with_only_supported_gates_is_not_changed(self):
        original_circuit = circuits.Circuit(
            [
                circuits.X(0),
                circuits.RX(np.pi)(2),
                circuits.SWAP(3, 0),
                circuits.RY(0.5).controlled(1)(0, 2),
            ]
        )
        assert make_circuit_qhipster_compatible(original_circuit) == original_circuit

    def test_identity_gates_are_replaced_with_zero_angle_rotation(self):
        identity_gate_indices = [0, 2]
        original_circuit = circuits.Circuit(
            [circuits.I(0), circuits.X(1), circuits.I(2), circuits.RX(0)(2)]
        )
        compatible_circuit = make_circuit_qhipster_compatible(original_circuit)

        assert all(
            compatible_circuit.operations[i].gate == circuits.RX(0)
            and compatible_circuit.operations[i].qubit_indices
            == original_circuit.operations[i].qubit_indices
            for i in identity_gate_indices
        )

    def test_supported_gates_are_left_unchanged(self):
        supported_gate_indices = [1, 3]
        original_circuit = circuits.Circuit(
            [circuits.I(0), circuits.X(1), circuits.I(2), circuits.RX(0)(2)]
        )
        compatible_circuit = make_circuit_qhipster_compatible(original_circuit)

        all(
            compatible_circuit.operations[i] == original_circuit.operations[i]
            for i in supported_gate_indices
        )

    @pytest.mark.parametrize(
        "supported_gate", [circuits.X, circuits.RZ(np.pi), circuits.H]
    )
    def test_circuit_with_iswap_gate_cannot_be_made_compatible(self, supported_gate):
        circuit = circuits.Circuit([circuits.ISWAP(0, 2), supported_gate(1)])

        with pytest.raises(NotImplementedError):
            make_circuit_qhipster_compatible(circuit)

    @pytest.mark.parametrize(
        "unsupported_gate",
        [
            circuits.XX(0.5),
            circuits.YY(sympy.Symbol("theta")),
            circuits.ZZ(0.1),
            circuits.XY(np.pi / 2),
        ],
    )
    @pytest.mark.parametrize(
        "supported_gate", [circuits.X, circuits.RZ(np.pi), circuits.H]
    )
    def test_circuit_with_two_qubit_pauli_rotation_cannot_be_made_compatible(
        self, supported_gate, unsupported_gate
    ):
        circuit = circuits.Circuit([unsupported_gate(0, 2), supported_gate(1)])

        with pytest.raises(NotImplementedError):
            make_circuit_qhipster_compatible(circuit)
