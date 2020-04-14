# qe-qhipster

## What is it?


`qe-qhipster` is an [Orquestra](https://www.zapatacomputing.com/orquestra/) module, which allows to users to integrate workflow componetns with the Intel [qHiPSTER](https://github.com/iqusoft/intel-qs) simulator.
It complies to the backend interface defined in the [`z-quantum-core`](https://github.com/zapatacomputing/z-quantum-core/blob/master/src/python/orquestra/core/interfaces/backend.py).

## Usage

### Workflow
In order to use `qe-qhipster` in your workflow, you need to add it as a resource:

```yaml
resources:
- name: qe-qhipster
  type: git
  parameters:
    url: "git@github.com:zapatacomputing/qe-qhipster.git"
    branch: "master"
```

and then import in a specific step:

```yaml
- - name: my-task
    template: template-1
    arguments:
      parameters:
      - backend-specs: "{'module_name': 'orquestra.forest.simulator', 'function_name': 'QHipsterSimulator'}"
      - resources: [qe-qhipster]
```

### Task

In order to use qHiPSTER, a script performing initialization must be executed first. It needs to be done inside the task in the `artifacts` section:

```yaml
      artifacts:
      - name: main-script
        path: /app/main_script.sh
        raw:
          data: |
            source /app/usr/local/bin/compilers_and_libraries.sh
            python3 python_script.py
```

Then to use backend in the python code we can either simply create an object:

```python
from qe.qhipster import QHipsterSimulator
backend = QHipsterSimulator()
```

or use `backend-specs` parameter to make our code work with other backends too:

```python
from zquantum.core.utils import create_object
backend_specs = {{inputs.parameters.backend-specs}}
backend = create_object(backend_specs)
```

## Development and contribution

You can find the development guidelines in the [`z-quantum-core` repository](https://github.com/zapatacomputing/z-quantum-core).

### Tests
Since qHiPSTER requires compiled binaries, it cannot be executed locally (unless you have aforementioned binaries). Therefore, in order to run tests on your machine, you need perform the following steps:

- pull the docker image zapatacomputing/qe_qhipster
- run a docker container for the above image
- download and install the `z-quantum-core` resource in said container
- download and install the `qe-qhipster` resource in said container
- run `python3 -m pytest` from the `qe-qhipster` resource `src/` directory
