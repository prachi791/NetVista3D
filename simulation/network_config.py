
# NetVista 3D: DV vs LS Investigation

NODES = ["A", "B", "C", "D", "E"]

# Each link is bidirectional: (router 1, router 2, cost)
LINKS = [
    ("A", "B", 2),
    ("A", "C", 5),
    ("B", "C", 1),
    ("B", "D", 2),
    ("C", "D", 3),
    ("C", "E", 1),
    ("D", "E", 2),
]

# Link to remove during the failure experiment
LINK_CHANGE = ("B", "D")
