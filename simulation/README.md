# NetVista 3D — Simulation Documentation

## 1. Overview

This directory contains the Python implementation for the NetVista 3D advanced investigation, **Distance Vector (DV) vs Link State (LS) Update Overhead and Convergence**.

The simulation compares simplified synchronous routing models using a five-node network. It records message transmission attempts, convergence rounds, and route-validation results across three experiment scenarios.

## 2. Files and Directories

```text
simulation/
├── README.md
├── main.py
├── main_checkpoint.py
├── network_config.py
├── generate_graphs.py
├── requirements.txt
└── results/
    ├── results.csv
    └── graphs/
        ├── message_overhead.png
        └── convergence_rounds.png
```

- `main.py` — simulation entry point.
- `main_checkpoint.py` — checkpoint copy of the simulation, if retained in the project.
- `network_config.py` — network topology and link-failure configuration.
- `generate_graphs.py` — reads the recorded CSV and generates comparison graphs.
- `requirements.txt` — Python dependency list.
- `results/results.csv` — recorded experiment measurements.
- `results/graphs/` — generated graph images.

Check the actual files in this directory before running the commands below. The checkpoint file is not required for the standard workflow unless the implementation specifically depends on it.

## 3. Network Configuration

The simulation uses five nodes:

`A, B, C, D, E`

The configured links and costs are:

| Link | Cost |
|---|---:|
| A–B | 2 |
| A–C | 5 |
| B–C | 1 |
| B–D | 2 |
| C–D | 3 |
| C–E | 1 |
| D–E | 2 |

The failure scenario removes the B–D link.

## 4. Experiment Scenarios

The recorded experiments cover:

1. **Baseline:** Routing operation using the original topology.
2. **Fresh start after failure:** Routing started with the failed-link topology.
3. **Recovery after failure:** Routing tables or link-state information are updated after a link failure according to each model's implementation.

The exact initialization, update procedure, stopping conditions, and message-counting rules are defined by the source code.

## 5. Recorded Results

| Scenario | Algorithm | Rounds | Message attempts |
|---|---|---:|---:|
| Baseline | DV | 3 | 42 |
| Baseline | LS | 3 | 50 |
| Fresh start after failure | DV | 3 | 36 |
| Fresh start after failure | LS | 3 | 40 |
| Recovery after failure | DV | 3 | 36 |
| Recovery after failure | LS | 3 | 16 |

All six recorded experiment rows passed the implemented distance and next-hop validation checks.

### Interpreting the measurements

- DV counts distance-vector advertisement attempts according to its implementation.
- LS counts link-state advertisement transmission attempts according to its implementation.
- These message counts are not byte counts or direct measurements of bandwidth consumption.
- The models use different round-counting conventions. Equal reported round counts do not establish equivalent real-world convergence speed.
- The lower LS message count in the recovery scenario applies to this tested topology and implementation; it does not prove universal superiority.

## 6. Setup

Install a compatible Python version and open a terminal in this `simulation/` directory.

If a virtual environment is desired, create and activate it using the commands appropriate for your operating system.

Install the dependencies listed in `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

If the dependency file is missing or incomplete, inspect the imports in the Python source before installing additional packages.

## 7. Run the Simulation

From the `simulation/` directory, run:

```bash
python main.py
```

This command assumes that `main.py` is the correct entry point and that its imports and file paths match the project layout. Check the source code if execution fails.

The expected experiment output is:

`results/results.csv`

The program may overwrite the existing CSV when it runs. Preserve a copy of the recorded dataset before rerunning if you need to retain the original submitted measurements.

## 8. Generate the Graphs

After the CSV has been generated, run:

```bash
python generate_graphs.py
```

The graph-generation script reads `results/results.csv` and writes:

- `results/graphs/message_overhead.png`
- `results/graphs/convergence_rounds.png`

Ensure the CSV exists and contains the expected experiment records before generating the graphs.

## 9. Reproducibility Checklist

- [ ] Python and required dependencies are installed.
- [ ] `main.py` and its required configuration files are present.
- [ ] The simulation runs successfully.
- [ ] The generated CSV contains the expected experiment records.
- [ ] Both graph files are generated successfully.
- [ ] Distance and next-hop validation results are checked.
- [ ] The report, graphs, and CSV are consistent with the recorded results.

## 10. Limitations

This project implements simplified educational routing models over a five-node network. Its results are specific to the implemented topology, scenarios, initialization procedures, message-counting definitions, and stopping conditions.

The experiment does not directly measure real-world network latency, bytes transferred, CPU cost, or wall-clock convergence time.

---

**Project:** NetVista 3D  
**Course:** Fundamentals of Computer Networks (ITUC201)  
**Student:** Prachi Modi  
**Student ID:** 25CS045