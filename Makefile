include subtrees/z_quantum_actions/Makefile

github_actions:
	apt-get update
	apt-get install -y python3.7-venv

	@echo "LOOOK HERE FOR NUMPY VERISON"
	python3 -c "import numpy; print(numpy.version.version)"

	python3 -m venv ${VENV} && \
		${VENV}/bin/python3 -m pip install --upgrade pip && \
		${VENV}/bin/python3 -m pip install ./z-quantum-core && \
		${VENV}/bin/python3 -m pip install -e '.[develop]'
