import os
import subprocess

from zquantum.core.interfaces.backend import QuantumSimulator
from zquantum.core.circuit import save_circuit
from zquantum.core.measurement import (
    load_wavefunction,
    load_expectation_values,
    sample_from_wavefunction,
    Measurements,
)
from .utils import save_symbolic_operator
from openfermion.ops import SymbolicOperator
import numpy as np


class QHipsterSimulator(QuantumSimulator):
    def __init__(self, n_samples=None, nthreads=1):
        self.nthreads = nthreads
        self.n_samples = n_samples

        # NOTE: The environment variables that are set below are necessary for running qhipster with the intel psxe
        #   runtime installation. They were obtained through sourcing the script
        #   /app/usr/local/bin/compilers_and_library.sh which can be found in the zapatacomputing/qe-qhipster docker
        #   image.
        os.putenv(
            "LD_LIBRARY_PATH",
            "/opt/intel/psxe_runtime_2019.3.199/linux/daal/lib/intel64_lin:/opt/intel/psxe_runtime_2019.3.199/linux/compiler/lib/intel64_lin:/opt/intel/psxe_runtime_2019.3.199/linux/mkl/lib/intel64_lin:/opt/intel/psxe_runtime_2019.3.199/linux/tbb/lib/intel64/gcc4.7:/opt/intel/psxe_runtime_2019.3.199/linux/ipp/lib/intel64:/opt/intel/psxe_runtime_2019.3.199/linux/mpi/intel64/libfabric/lib:/opt/intel/psxe_runtime_2019.3.199/linux/mpi/intel64/lib/release:/opt/intel/psxe_runtime_2019.3.199/linux/mpi/intel64/lib:/opt/intel/psxe_runtime_2019.3.199/linux/compiler/lib/intel64_lin",
        )
        os.putenv("IPPROOT", "/opt/intel/psxe_runtime_2019.3.199/linux/ipp")
        os.putenv(
            "FI_PROVIDER_PATH",
            "/opt/intel/psxe_runtime_2019.3.199/linux/mpi/intel64/libfabric/lib/prov",
        )
        os.putenv(
            "CLASSPATH",
            "/opt/intel/psxe_runtime_2019.3.199/linux/daal/lib/daal.jar:/opt/intel/psxe_runtime_2019.3.199/linux/mpi/intel64/lib/mpi.jar",
        )
        os.putenv(
            "CPATH",
            "/opt/intel/psxe_runtime_2019.3.199/linux/daal/include:/opt/intel/psxe_runtime_2019.3.199/linux/mkl/include:/opt/intel/psxe_runtime_2019.3.199/linux/tbb/include:/opt/intel/psxe_runtime_2019.3.199/linux/ipp/include:",
        )
        os.putenv(
            "NLSPATH",
            "/opt/intel/psxe_runtime_2019.3.199/linux/mkl/lib/intel64_lin/locale/%l_%t/%N:/opt/intel/psxe_runtime_2019.3.199/linux/compiler/lib/intel64_lin/locale/%l_%t/%N",
        )
        os.putenv(
            "LIBRARY_PATH",
            "/opt/intel/psxe_runtime_2019.3.199/linux/daal/lib/intel64_lin:/opt/intel/psxe_runtime_2019.3.199/linux/compiler/lib/intel64_lin:/opt/intel/psxe_runtime_2019.3.199/linux/mkl/lib/intel64_lin:/opt/intel/psxe_runtime_2019.3.199/linux/tbb/lib/intel64/gcc4.7:/opt/intel/psxe_runtime_2019.3.199/linux/ipp/lib/intel64:/opt/intel/psxe_runtime_2019.3.199/linux/mpi/intel64/libfabric/lib:/opt/intel/psxe_runtime_2019.3.199/linux/compiler/lib/intel64_lin",
        )
        os.putenv("DAALROOT", "/opt/intel/psxe_runtime_2019.3.199/linux/daal")
        os.putenv(
            "MIC_LD_LIBRARY_PATH",
            "/opt/intel/psxe_runtime_2019.3.199/linux/compiler/lib/intel64_lin_mic",
        )
        os.putenv("MANPATH", "/opt/intel/psxe_runtime_2019.3.199/linux/mpi/man:")
        os.putenv("CPLUS_INCLUDE_PATH", "/app/json_parser/include")
        os.putenv("MKLROOT", "/opt/intel/psxe_runtime_2019.3.199/linux/mkl")
        os.putenv(
            "PATH",
            "/opt/intel/psxe_runtime_2019.3.199/linux/mpi/intel64/libfabric/bin:/opt/intel/psxe_runtime_2019.3.199/linux/mpi/intel64/bin:/opt/intel/psxe_runtime_2019.3.199/linux/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        )
        os.putenv("TBBROOT", "/opt/intel/psxe_runtime_2019.3.199/linux/tbb")
        os.putenv(
            "PKG_CONFIG_PATH",
            "/opt/intel/psxe_runtime_2019.3.199/linux/mkl/bin/pkgconfig",
        )
        os.putenv("I_MPI_ROOT", "/opt/intel/psxe_runtime_2019.3.199/linux/mpi")

    def run_circuit_and_measure(self, circuit, **kwargs):
        wavefunction = self.get_wavefunction(circuit)
        return Measurements(sample_from_wavefunction(wavefunction, self.n_samples))

    def get_expectation_values(self, circuit, qubit_operator, **kwargs):
        return self.get_exact_expectation_values(circuit, qubit_operator, **kwargs)

    def get_exact_expectation_values(self, circuit, qubit_operator, **kwargs):
        save_circuit(circuit, "./temp_qhipster_circuit.json")
        if isinstance(qubit_operator, SymbolicOperator):
            save_symbolic_operator(qubit_operator, "./temp_qhipster_operator.json")
        else:
            raise Exception(
                "Unsupported type: "
                + type(qubit_operator)
                + "QHipster works only with openfermion.SymbolicOperator"
            )

        # Parse JSON files for qhipster usage
        subprocess.call(
            ["/app/json_parser/json_to_qasm.o", "./temp_qhipster_circuit.json"]
        )
        subprocess.call(
            [
                "/app/json_parser/qubitop_to_paulistrings.o",
                "./temp_qhipster_operator.json",
            ]
        )
        # Run simulation
        subprocess.call(
            [
                "/app/zapata/zapata_interpreter_no_mpi_get_exp_vals.out",
                "./temp_qhipster_circuit.txt",
                str(self.nthreads),
                "./temp_qhipster_operator.txt",
                "./expectation_values.json",
            ]
        )
        expectation_values = load_expectation_values("./expectation_values.json")
        term_index = 0
        for term in qubit_operator.terms:
            expectation_values.values[term_index] = np.real(
                qubit_operator.terms[term] * expectation_values.values[term_index]
            )
            term_index += 1
        return expectation_values

    def get_wavefunction(self, circuit):
        # First, save the circuit object to file in JSON format
        save_circuit(circuit, "./temp_qhipster_circuit.json")

        # Parse JSON files for qhipster usage
        subprocess.call(
            ["/app/json_parser/json_to_qasm.o", "./temp_qhipster_circuit.json"]
        )
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
        os.remove("./temp_qhipster_circuit.json")
        os.remove("./temp_qhipster_wavefunction.json")
        return wavefunction
