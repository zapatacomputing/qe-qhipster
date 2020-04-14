from openfermion import SymbolicOperator
import numpy as np
import json


def save_symbolic_operator(op: SymbolicOperator, filename: str) -> None:
    dictionary = {}
    dictionary['expression'] = convert_symbolic_op_to_string(op)

    with open(filename, 'w') as f:
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
        return '0'
    string_rep = ''
    for term, coeff in op.terms.items():
        if np.abs(coeff) < 0.00000001:
            continue
        tmp_string = '{} ['.format(coeff)
        for factor in term:
            index, action = factor
            action_string = op.action_strings[op.actions.index(action)]
            if op.action_before_index:
                tmp_string += '{}{} '.format(action_string, index)
            else:
                tmp_string += '{}{} '.format(index, action_string)
        string_rep += '{}] +\n'.format(tmp_string.strip())
    return string_rep[:-3]