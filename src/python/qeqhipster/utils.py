import json

import numpy as np
from zquantum.core import circuits
from zquantum.core.openfermion import SymbolicOperator


def save_symbolic_operator(op: SymbolicOperator, filename: str) -> None:
    dictionary = {"expression": convert_symbolic_op_to_string(op)}
    with open(filename, "w") as f:
        f.write(json.dumps(dictionary, indent=2))


def convert_symbolic_op_to_string(op: SymbolicOperator) -> str:
    """Convert an openfermion SymbolicOperator to a string. This differs from the
    SymbolicOperator's __str__ method only in that we preserve the order of terms.
    Adapted from openfermion.

    Args:
        op (openfermion.ops.SymbolicOperator): the operator

    Returns
        string: the string representation of the operator
    """
    if not op.terms:
        return "0"
    string_rep = ""
    for term, coeff in op.terms.items():
        if np.abs(coeff) < 0.00000001:
            continue
        tmp_string = "{} [".format(coeff)
        for factor in term:
            index, action = factor
            action_string = op.action_strings[op.actions.index(action)]
            if op.action_before_index:
                tmp_string += "{}{} ".format(action_string, index)
            else:
                tmp_string += "{}{} ".format(index, action_string)
        string_rep += "{}] +\n".format(tmp_string.strip())
    return string_rep[:-3]


QHIPSTER_UNSUPPORTED_GATES = {"ISWAP", "XX", "YY", "ZZ", "XY"}


def make_circuit_qhipster_compatible(circuit: circuits.Circuit):
    unsupported_operations = [
        op for op in circuit.operations if op.gate.name in QHIPSTER_UNSUPPORTED_GATES
    ]
    if unsupported_operations:
        raise NotImplementedError(
            "ISWAP gates and two-qubit Pauli rotations are not supported by qHipster "
            f"integration. Offending operations: {unsupported_operations}."
        )
    return circuits.Circuit(
        operations=[
            circuits.RX(0)(*op.qubit_indices) if op.gate.name == "I" else op
            for op in circuit.operations
        ],
        n_qubits=circuit.n_qubits,
    )


GATE_NAME_SPECIAL_CASES = {"RX": "Rx", "RY": "Ry", "RZ": "Rz"}


def _qhipster_gate_name(gate: circuits.Gate):
    return GATE_NAME_SPECIAL_CASES.get(gate.name, gate.name.upper())


def _serialize_operation_to_qasm(operation: circuits.GateOperation):
    operation_param_string = " ".join(
        [
            *(f"{param:.20f}" for param in operation.params),
            *map(str, operation.qubit_indices),
        ]
    )
    return f"{_qhipster_gate_name(operation.gate)} {operation_param_string}"


def convert_to_simplified_qasm(circuit: circuits.Circuit):
    return (
        "\n".join(
            [
                f"{max(index for op in circuit.operations for index in op.qubit_indices)+1}",  # noqa: E501
                *map(_serialize_operation_to_qasm, circuit.operations),
            ]
        )
        if circuit.operations
        else "0\n"
    )
