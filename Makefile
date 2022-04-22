include subtrees/z_quantum_actions/Makefile

github_actions:
	apt-get update
	apt-get install -y python3.7-venv

	# For some reason, having numpy installed globally makes mypy fail.
	python3 -m pip uninstall -y numpy

	python3 -m venv ${VENV} && \
		${VENV}/bin/python3 -m pip install --upgrade pip && \
		${VENV}/bin/python3 -m pip install ./z-quantum-core && \
		${VENV}/bin/python3 -m pip install -e '.[develop]'


build-system-deps:
	$(PYTHON) -m pip install setuptools wheel "setuptools_scm>=6.0"
