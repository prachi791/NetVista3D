# NetVista 3D — Advanced FCN Investigation

**Project:** Advanced DV vs LS Update Overhead and Convergence  
**Student:** Prachi Modi  
**Student ID:** 25CS045  
**Course:** Fundamentals of Computer Networks (ITUC201)  
**Institution:** CSPIT, CHARUSAT University  
**Project Type:** Advanced Investigation

---

## 1. Project Overview

NetVista 3D is an educational computer networking investigation comparing simplified Distance Vector (DV) and Link State (LS) routing models.

The project examines message transmission overhead, convergence rounds, and route-validation results across three scenarios: baseline operation, fresh start after a link failure, and recovery after a link failure.

The project consists of two main components:

- **Website:** An interactive interface for presenting the investigation, topology, results, graphs, and submission deliverables.
- **Simulation:** Python source code and supporting files used to run the experiments and generate the recorded measurements.

## 2. Project Structure

```text
NetVista3D/
├── README.md
├── .gitignore
├── website/
│   ├── index.html
│   ├── viewer.html
│   ├── css/
│   ├── js/
│   ├── assets/
│   │   └── results/
│   │       ├── message_overhead.png
│   │       └── convergence_rounds.png
│   └── downloads/
│       ├── technical_report.pdf
│       └── results.csv
└── simulation/
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

This structure describes the intended organization. Retain any additional files required by the actual website or simulation, and ensure the referenced files exist before publishing.

## 3. Website

The website presents the project overview, assumptions, network topology, simulation methodology, results, analysis, and submission deliverables.

The `website/` directory contains the website files and the copies of the report, CSV, and graph images used for online viewing.

### Accessing the website

**Live website:** Add the published website URL here after deployment.

To test the website locally, open a terminal in the `website/` directory and run:

```bash
python -m http.server 8080
```

Then open:

`http://localhost:8080/`

This local address is for testing on your computer. Share the published URL with your professor after deployment.

## 4. Simulation

The `simulation/` directory contains the Python implementation, network configuration, dependencies, experiment data, and graph-generation script.

For setup instructions and experiment reproduction, see [`simulation/README.md`](simulation/README.md).

## 5. Recorded Experimental Results

The simulation recorded the following results:

| Scenario | Algorithm | Rounds | Message attempts |
|---|---|---:|---:|
| Baseline | DV | 3 | 42 |
| Baseline | LS | 3 | 50 |
| Fresh start after failure | DV | 3 | 36 |
| Fresh start after failure | LS | 3 | 40 |
| Recovery after failure | DV | 3 | 36 |
| Recovery after failure | LS | 3 | 16 |

All six recorded experiment rows passed the implemented distance and next-hop validation checks.

Message counts represent transmission attempts counted by the simulation. They do not directly measure bytes transmitted, actual bandwidth consumption, or wall-clock convergence time.

The algorithms use different counting and stopping conventions, so equal round counts should not be interpreted as proof of equal real-world convergence speed.

## 6. Deliverables

The project submission includes the following items, as applicable to the final submission:

- Technical report in PDF format.
- Python simulation source code and network configuration.
- Recorded experimental CSV dataset.
- Message-overhead and convergence-rounds graphs.
- Graph-generation script and dependency information.
- Narrated project presentation video.
- Completed student submission proforma.

The final report and CSV are available through the website's deliverables section when the website assets and links have been configured.

## 7. Limitations

This is a simplified educational simulation using a five-node network. Its findings apply to the implemented models, topology, scenarios, and counting rules.

The results should not be generalized to every network topology or production implementation of Distance Vector and Link State routing.

## 8. Reproducibility and Integrity

The experiment data and graphs should be generated from the simulation source code. The recorded measurements must not be manually altered to improve the appearance of a graph or the apparent performance of an algorithm.

See the simulation README for setup and execution instructions.

---

**NetVista 3D — Fundamentals of Computer Networks (ITUC201)**