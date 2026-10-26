import heapq
from math import inf

import networkx as nx

from network_config import NODES, LINKS, LINK_CHANGE


# --------------------------------------------------
# 1. NETWORK CONFIGURATION HELPERS
# --------------------------------------------------

def build_adjacency(links=None):
    """Build a bidirectional network from the supplied links."""
    if links is None:
        links = LINKS

    adjacency = {node: {} for node in NODES}

    for u, v, cost in links:
        adjacency[u][v] = cost
        adjacency[v][u] = cost

    return adjacency


def remove_link(links, failed_link):
    """Return a new link list without the failed bidirectional link."""
    u, v = failed_link

    return [
        (a, b, cost)
        for a, b, cost in links
        if {a, b} != {u, v}
    ]


# --------------------------------------------------
# 2. INDEPENDENT DISTANCE VALIDATION
# --------------------------------------------------

def validate_distances(adjacency, distances, algorithm_name="Routing"):
    """Compare routing costs with NetworkX shortest-path costs."""
    graph = nx.Graph()
    graph.add_nodes_from(NODES)

    for node, neighbours in adjacency.items():
        for neighbour, cost in neighbours.items():
            graph.add_edge(node, neighbour, weight=cost)

    all_correct = True

    print(f"\nIndependent {algorithm_name} distance validation:")

    for source in NODES:
        reference = nx.single_source_dijkstra_path_length(
            graph, source, weight="weight"
        )

        for destination in NODES:
            actual = distances[source][destination]
            expected = reference.get(destination, inf)

            if actual != expected:
                all_correct = False
                print(
                    f"FAIL: {source} -> {destination}: "
                    f"actual={actual}, expected={expected}"
                )

    if all_correct:
        print(
            f"PASS: All {algorithm_name} distance costs "
            "match NetworkX."
        )
    else:
        print(f"FAIL: {algorithm_name} distance validation failed.")

    return all_correct


# --------------------------------------------------
# 3. DISTANCE VECTOR (DV)
# --------------------------------------------------

def initialise_routing_tables(adjacency):
    """Initially, each router knows only itself and direct neighbours."""
    distances = {}
    next_hops = {}

    for node in NODES:
        distances[node] = {}
        next_hops[node] = {}

        for destination in NODES:
            if destination == node:
                distances[node][destination] = 0
                next_hops[node][destination] = node

            elif destination in adjacency[node]:
                distances[node][destination] = adjacency[node][destination]
                next_hops[node][destination] = destination

            else:
                distances[node][destination] = inf
                next_hops[node][destination] = None

    return distances, next_hops


def run_distance_vector(links=None, experiment_name="DV"):
    """Run synchronous DV until a complete round has no cost changes."""
    adjacency = build_adjacency(links)

    distances, next_hops = initialise_routing_tables(adjacency)

    rounds = 0
    update_messages = 0

    print(f"\n{experiment_name}: Distance Vector")

    while True:
        # Freeze the tables at the start of the round.
        old_distances = {
            node: distances[node].copy()
            for node in NODES
        }

        old_next_hops = {
            node: next_hops[node].copy()
            for node in NODES
        }

        new_distances = {
            node: old_distances[node].copy()
            for node in NODES
        }

        new_next_hops = {
            node: old_next_hops[node].copy()
            for node in NODES
        }

        changed = False
        rounds += 1

        for node in NODES:
            for neighbour, link_cost in adjacency[node].items():

                # Count one advertisement per directed neighbour link.
                update_messages += 1

                for destination in NODES:
                    neighbour_cost = old_distances[neighbour][destination]

                    if neighbour_cost == inf:
                        continue

                    candidate = link_cost + neighbour_cost

                    if candidate < new_distances[node][destination]:
                        new_distances[node][destination] = candidate
                        new_next_hops[node][destination] = neighbour
                        changed = True

        distances = new_distances
        next_hops = new_next_hops

        print(
            f"Round {rounds}: "
            f"{'routes updated' if changed else 'no changes'}"
        )

        if not changed:
            break

    validate_distances(adjacency, distances, "DV")

    print("\nDV routing tables:")

    for node in NODES:
        print(f"\nRouter {node}")
        print(f"{'Destination':<14}{'Cost':<10}{'Next hop'}")

        for destination in NODES:
            cost = distances[node][destination]
            hop = next_hops[node][destination]

            cost_text = "∞" if cost == inf else str(cost)
            hop_text = "-" if hop is None else hop

            print(f"{destination:<14}{cost_text:<10}{hop_text}")

    print("\nDV measurements")
    print("Convergence rounds:", rounds)
    print("Update messages:", update_messages)

    return distances, next_hops, rounds, update_messages


# --------------------------------------------------
# 4. DIJKSTRA'S SHORTEST-PATH ALGORITHM
# --------------------------------------------------

def dijkstra(graph, source):
    """Calculate shortest distances and paths from one router."""
    distances = {node: inf for node in graph}
    paths = {node: [] for node in graph}

    distances[source] = 0
    paths[source] = [source]

    priority_queue = [(0, source)]

    while priority_queue:
        current_cost, current = heapq.heappop(priority_queue)

        if current_cost != distances[current]:
            continue

        for neighbour, link_cost in graph[current].items():
            candidate = current_cost + link_cost

            if candidate < distances[neighbour]:
                distances[neighbour] = candidate
                paths[neighbour] = paths[current] + [neighbour]

                heapq.heappush(
                    priority_queue,
                    (candidate, neighbour)
                )

    return distances, paths


# --------------------------------------------------
# 5. LINK STATE (LS)
# --------------------------------------------------

def run_link_state(links=None, experiment_name="LS"):
    """
    Flood LSAs synchronously.
    Each LSA carries its origin router's direct links and costs.
    Each router reconstructs its own graph from received LSAs.
    """
    adjacency = build_adjacency(links)

    # Each LSA contains the origin router's actual link information.
    # Example: LSA for A might contain {'B': 2, 'C': 5}.
    lsas = {
        node: dict(adjacency[node])
        for node in NODES
    }

    # Each router initially knows only its own LSA.
    known_lsas = {
        node: {node}
        for node in NODES
    }

    # Each frontier maps an LSA origin to the neighbour it came from.
    frontier = {
        node: {node: None}
        for node in NODES
    }

    rounds = 0
    update_messages = 0

    while any(frontier[node] for node in NODES):
        next_frontier = {
            node: {}
            for node in NODES
        }

        rounds += 1

        # Every router forwards only LSAs available at round start.
        for node in NODES:
            for origin, incoming_neighbour in frontier[node].items():

                for neighbour in adjacency[node]:

                    # Do not send the LSA directly back to its sender.
                    if neighbour == incoming_neighbour:
                        continue

                    # Count each transmission attempt, including
                    # advertisements received by routers that know
                    # that origin already.
                    update_messages += 1

                    if origin not in known_lsas[neighbour]:
                        if origin not in next_frontier[neighbour]:
                            next_frontier[neighbour][origin] = node

        # Newly received LSAs become known after this round completes.
        for node in NODES:
            for origin in next_frontier[node]:
                known_lsas[node].add(origin)

        frontier = next_frontier

    # Each router constructs a separate map using its received LSAs.
    all_distances = {}
    all_next_hops = {}

    for source in NODES:
        if known_lsas[source] != set(NODES):
            missing = set(NODES) - known_lsas[source]
            raise RuntimeError(
                f"Router {source} is missing LSAs from {sorted(missing)}."
            )

        learned_graph = {
            node: {}
            for node in NODES
        }

        # Use advertised information only, not the shared adjacency map.
        for origin in known_lsas[source]:
            for neighbour, cost in lsas[origin].items():
                learned_graph[origin][neighbour] = cost

        distances, paths = dijkstra(learned_graph, source)

        all_distances[source] = distances
        all_next_hops[source] = {}

        for destination in NODES:
            path = paths[destination]

            if source == destination:
                all_next_hops[source][destination] = source
            elif path:
                all_next_hops[source][destination] = path[1]
            else:
                all_next_hops[source][destination] = None

    print(f"\n{experiment_name}: Link State")
    print("LS flooding completed.")
    print("Flooding rounds:", rounds)
    print("LSA transmissions:", update_messages)

    validate_distances(adjacency, all_distances, "LS")

    print("\nLS routing tables:")

    for source in NODES:
        print(f"\nRouter {source}")
        print(f"{'Destination':<14}{'Cost':<10}{'Next hop'}")

        for destination in NODES:
            cost = all_distances[source][destination]
            hop = all_next_hops[source][destination]

            cost_text = "∞" if cost == inf else str(cost)
            hop_text = "-" if hop is None else hop

            print(f"{destination:<14}{cost_text:<10}{hop_text}")

    print("\nLS measurements")
    print("Flooding rounds:", rounds)
    print("LSA transmissions:", update_messages)

    return all_distances, all_next_hops, rounds, update_messages


# --------------------------------------------------
# 6. RUN THE FOUR BASELINE AND CHANGED-TOPOLOGY TESTS
# --------------------------------------------------

if __name__ == "__main__":

    print("\n=== Baseline network: DV ===")
    run_distance_vector(LINKS, "Baseline DV")

    print("\n=== Baseline network: LS ===")
    run_link_state(LINKS, "Baseline LS")

    changed_links = remove_link(LINKS, LINK_CHANGE)

    print("\n=== After B-D failure: DV ===")
    run_distance_vector(changed_links, "Failure DV")

    print("\n=== After B-D failure: LS ===")
    run_link_state(changed_links, "Failure LS")
