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
from zquantum.core.circuits import Circuit
from .utils import (
    save_symbolic_operator,
    make_circuit_qhipster_compatible,
    convert_to_simplified_qasm,
)
from openfermion.ops import SymbolicOperator
import numpy as np


# NOTE: The environment variables below are necessary for running qhipster with the intel
# psxe runtime installation. They were obtained through sourcing the script
# /app/usr/local/bin/compilers_and_libraries.sh which can be found in the
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

    def run_circuit_and_measure(self, circuit, n_samples=None, **kwargs):
        if n_samples is None:
            n_samples = self.n_samples
        wavefunction = self.get_wavefunction(circuit)
        return Measurements(sample_from_wavefunction(wavefunction, n_samples))

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

            if not isinstance(qubit_operator, SymbolicOperator):
                raise TypeError(
                    f"Unsupported type: {type(qubit_operator)} QHipster works only with "
                    "openfermion.SymbolicOperator"
                )

            save_symbolic_operator(qubit_operator, operator_json_path)

            with open(circuit_txt_path, "w") as qasm_file:
                qasm_file.write(convert_to_simplified_qasm(circuit))

            subprocess.run(
                [
                    "/app/json_parser/qubitop_to_paulistrings.o",
                    operator_json_path,
                ],
                check=True,
            )
            # Run simulation
            subprocess.run(
                [
                    "/app/zapata/zapata_interpreter_no_mpi_get_exp_vals.out",
                    circuit_txt_path,
                    str(self.nthreads),
                    operator_txt_path,
                    expectation_values_json_path,
                ],
                env=PSXE_ENVS,
                check=True,
            )
            expectation_values = load_expectation_values(expectation_values_json_path)

        for term_index, term in enumerate(qubit_operator.terms):
            expectation_values.values[term_index] = np.real(
                qubit_operator.terms[term] * expectation_values.values[term_index]
            )
        return expectation_values

    def get_wavefunction(self, circuit):
        super().get_wavefunction(circuit)

        with tempfile.TemporaryDirectory() as dir_path:
            circuit_txt_path = os.path.join(dir_path, "temp_qhipster_circuit.txt")
            wavefunction_json_path = os.path.join(
                dir_path, "temp_qhipster_wavefunction.json"
            )

            circuit = make_circuit_qhipster_compatible(circuit)

            with open(circuit_txt_path, "w") as qasm_file:
                qasm_file.write(convert_to_simplified_qasm(circuit))

            # Run simulation
            subprocess.run(
                [
                    "/app/zapata/zapata_interpreter_no_mpi_get_wf.out",
                    circuit_txt_path,
                    str(self.nthreads),
                    wavefunction_json_path,
                ],
                env=PSXE_ENVS,
                check=True,
            )

            wavefunction = load_wavefunction(wavefunction_json_path)

        return wavefunction
