import os
import subprocess
import tempfile

from zquantum.core.interfaces.backend import QuantumSimulator
from zquantum.core.measurement import (
    load_wavefunction,
    load_expectation_values,
    sample_from_wavefunction,
    Measurements,
)
from zquantum.core.circuit import Circuit as OldCircuit
from zquantum.core.wip.compatibility_tools import compatible_with_old_type
from zquantum.core.wip.circuits import new_circuit_from_old_circuit
from .utils import (
    save_symbolic_operator,
    make_circuit_qhipster_compatible,
    convert_to_simplified_qasm,
)
from openfermion.ops import SymbolicOperator
import numpy as np


# NOTE: The environment variables below are necessary for running qhipster with the intel
# psxe runtime installation. They were obtained through sourcing the script
# /app/usr/local/bin/compilers_and_library.sh which can be found in the
# zapatacomputing/qe-qhipster docker image.


PSXE_BASE_PATH = "/opt/intel/psxe_runtime_2019.3.199/linux"


PSXE_ENVS = {
    "LD_LIBRARY_PATH": (
        f"{PSXE_BASE_PATH}/daal/lib/intel64_lin:"
        f"{PSXE_BASE_PATH}/compiler/lib/intel64_lin:"
        f"{PSXE_BASE_PATH}/mkl/lib/intel64_lin:"
        f"{PSXE_BASE_PATH}/tbb/lib/intel64/gcc4.7:"
        f"{PSXE_BASE_PATH}/ipp/lib/intel64:"
        f"{PSXE_BASE_PATH}/mpi/intel64/libfabric/lib:"
        f"{PSXE_BASE_PATH}/mpi/intel64/lib/release:"
        f"{PSXE_BASE_PATH}/mpi/intel64/lib:"
        f"{PSXE_BASE_PATH}/compiler/lib/intel64_lin"
    ),
    "IPPROOT": f"{PSXE_BASE_PATH}/ipp",
    "FI_PROVIDER_PATH": f"{PSXE_BASE_PATH}/mpi/intel64/libfabric/lib/prov",
    "CLASSPATH": (
        f"{PSXE_BASE_PATH}/daal/lib/daal.jar:"
        f"{PSXE_BASE_PATH}/mpi/intel64/lib/mpi.jar"
    ),
    "CPATH": (
        f"{PSXE_BASE_PATH}/daal/include:"
        f"{PSXE_BASE_PATH}/mkl/include:"
        f"{PSXE_BASE_PATH}/tbb/include:"
        f"{PSXE_BASE_PATH}/ipp/include:"
    ),
    "NLSPATH": (
        f"{PSXE_BASE_PATH}/mkl/lib/intel64_lin/locale/%l_%t/%N:"
        f"{PSXE_BASE_PATH}/compiler/lib/intel64_lin/locale/%l_%t/%N"
    ),
    "LIBRARY_PATH": (
        f"{PSXE_BASE_PATH}/daal/lib/intel64_lin:"
        f"{PSXE_BASE_PATH}/compiler/lib/intel64_lin:"
        f"{PSXE_BASE_PATH}/mkl/lib/intel64_lin:"
        f"{PSXE_BASE_PATH}/tbb/lib/intel64/gcc4.7:"
        f"{PSXE_BASE_PATH}/ipp/lib/intel64:"
        f"{PSXE_BASE_PATH}/mpi/intel64/libfabric/lib:"
        f"{PSXE_BASE_PATH}/compiler/lib/intel64_lin"
    ),
    "DAALROOT": f"{PSXE_BASE_PATH}/daal",
    "MIC_LD_LIBRARY_PATH": f"{PSXE_BASE_PATH}/compiler/lib/intel64_lin_mic",
    "MANPATH": f"{PSXE_BASE_PATH}/mpi/man:",
    "CPLUS_INCLUDE_PATH": "/app/json_parser/include",
    "MKLROOT": f"{PSXE_BASE_PATH}/mkl",
    "PATH": (
        f"{PSXE_BASE_PATH}/mpi/intel64/libfabric/bin:"
        f"{PSXE_BASE_PATH}/mpi/intel64/bin:"
        f"{PSXE_BASE_PATH}/bin:"
        "/usr/local/sbin:"
        "/usr/local/bin:"
        "/usr/sbin:"
        "/usr/bin:"
        "/sbin:"
        "/bin"
    ),
    "TBBROOT": f"{PSXE_BASE_PATH}/tbb",
    "PKG_CONFIG_PATH": f"{PSXE_BASE_PATH}/mkl/bin/pkgconfig",
    "I_MPI_ROOT": f"{PSXE_BASE_PATH}/mpi",
}


class QHipsterSimulator(QuantumSimulator):
    supports_batching = False

    def __init__(self, n_samples=None, nthreads=1):
        super().__init__(n_samples=n_samples)
        self.nthreads = nthreads

        for key, value in PSXE_ENVS.items():
            os.putenv(key, value)

    @compatible_with_old_type(
        old_type=OldCircuit, translate_old_to_wip=new_circuit_from_old_circuit
    )
    def run_circuit_and_measure(self, circuit, n_samples=None, **kwargs):
        if n_samples is None:
            n_samples = self.n_samples
        wavefunction = self.get_wavefunction(circuit)
        return Measurements(sample_from_wavefunction(wavefunction, n_samples))

    @compatible_with_old_type(
        old_type=OldCircuit, translate_old_to_wip=new_circuit_from_old_circuit
    )
    def get_exact_expectation_values(self, circuit, qubit_operator, **kwargs):
        self.number_of_circuits_run += 1
        self.number_of_jobs_run += 1
        circuit = make_circuit_qhipster_compatible(circuit)

        with tempfile.TemporaryDirectory() as dir_path:
            operator_json_path = os.path.join(dir_path, "temp_qhipster_operator.json")
            operator_txt_path = os.path.join(dir_path, "temp_qhipster_operator.txt")
            circuit_txt_path = os.path.join(dir_path, "temp_qhipster_circuit.txt")
            expectation_values_json_path = os.path.join(
                dir_path, "expectation_values.json"
            )

            if isinstance(qubit_operator, SymbolicOperator):
                save_symbolic_operator(qubit_operator, operator_json_path)
            else:
                raise Exception(
                    "Unsupported type: "
                    + type(qubit_operator)
                    + "QHipster works only with openfermion.SymbolicOperator"
                )

            with open(circuit_txt_path, "w") as qasm_file:
                qasm_file.write(convert_to_simplified_qasm(circuit))

            subprocess.call(
                [
                    "/app/json_parser/qubitop_to_paulistrings.o",
                    operator_json_path,
                ]
            )
            # Run simulation
            subprocess.call(
                [
                    "/app/zapata/zapata_interpreter_no_mpi_get_exp_vals.out",
                    circuit_txt_path,
                    str(self.nthreads),
                    operator_txt_path,
                    expectation_values_json_path,
                ]
            )
            expectation_values = load_expectation_values(expectation_values_json_path)

        term_index = 0
        for term in qubit_operator.terms:
            expectation_values.values[term_index] = np.real(
                qubit_operator.terms[term] * expectation_values.values[term_index]
            )
            term_index += 1
        return expectation_values

    @compatible_with_old_type(
        old_type=OldCircuit, translate_old_to_wip=new_circuit_from_old_circuit
    )
    def get_wavefunction(self, circuit):
        super().get_wavefunction(circuit)
        # First, save the circuit object to file in JSON format
        circuit = make_circuit_qhipster_compatible(circuit)

        with open("./temp_qhipster_circuit.txt", "w") as qasm_file:
            qasm_file.write(convert_to_simplified_qasm(circuit))

        # Run simulation
        subprocess.call(
            [
                "/app/zapata/zapata_interpreter_no_mpi_get_wf.out",
                "./temp_qhipster_circuit.txt",
                str(self.nthreads),
                "./temp_qhipster_wavefunction.json",
            ]
        )

        wavefunction = load_wavefunction("./temp_qhipster_wavefunction.json")
        os.remove("./temp_qhipster_wavefunction.json")
        return wavefunction
