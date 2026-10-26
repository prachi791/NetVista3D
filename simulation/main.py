import csv
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


def validate_next_hops(adjacency, distances, next_hops,
                       algorithm_name="Routing"):
    """Check that each next hop is valid and gives a shortest route."""

    all_valid = True

    for source in NODES:
        for destination in NODES:
            cost = distances[source][destination]
            hop = next_hops[source][destination]

            # A router's route to itself must have cost zero.
            if source == destination:
                if cost != 0 or hop != source:
                    all_valid = False
                    print(
                        f"FAIL: Invalid self-route at {source}"
                    )
                continue

            # Unreachable destinations must not have a next hop.
            if cost == inf:
                if hop is not None:
                    all_valid = False
                    print(
                        f"FAIL: {source} has an invalid next hop "
                        f"for unreachable destination {destination}"
                    )
                continue

            # A reachable destination needs a direct next hop.
            if hop not in adjacency[source]:
                all_valid = False
                print(
                    f"FAIL: {source} -> {destination}: "
                    f"{hop} is not an adjacent router"
                )
                continue

            # The first hop plus its remaining route must equal
            # the source's reported shortest-path distance.
            remaining_cost = distances[hop][destination]
            if remaining_cost == inf:
                all_valid = False
                print(
                    f"FAIL: {source} -> {destination}: "
                    "next hop cannot reach the destination"
                )
                continue

            route_cost = adjacency[source][hop] + remaining_cost

            if route_cost != cost:
                all_valid = False
                print(
                    f"FAIL: {source} -> {destination}: "
                    f"reported cost = {cost}, "
                    f"next-hop route cost = {route_cost}"
                )

    if all_valid:
        print(
            f"PASS: All {algorithm_name} next hops are valid "
            "and consistent with shortest-path costs."
        )
    else:
        print(
            f"FAIL: {algorithm_name} next-hop validation failed."
        )

    return all_valid


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


def check_experiment_results(adjacency, distances, next_hops):
    """Independently check shortest-path distances and next hops."""

    graph = nx.Graph()
    graph.add_nodes_from(NODES)

    for node in NODES:
        for neighbor, cost in adjacency[node].items():
            graph.add_edge(node, neighbor, weight=cost)

    distance_ok = True
    next_hop_ok = True

    for source in NODES:
        expected = nx.single_source_dijkstra_path_length(
            graph, source, weight="weight"
        )

        for destination in NODES:
            actual_cost = distances[source][destination]
            expected_cost = expected.get(destination, inf)

            if actual_cost != expected_cost:
                distance_ok = False

            hop = next_hops[source][destination]

            if source == destination:
                if actual_cost != 0 or hop != source:
                    next_hop_ok = False
                continue

            if expected_cost == inf:
                if hop is not None:
                    next_hop_ok = False
                continue

            if hop not in adjacency[source]:
                next_hop_ok = False
                continue

            remaining_cost = distances[hop][destination]

            if remaining_cost == inf:
                next_hop_ok = False
                continue

            route_cost = adjacency[source][hop] + remaining_cost

            if route_cost != actual_cost:
                next_hop_ok = False

    return distance_ok, next_hop_ok

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

    validate_next_hops(
    adjacency, distances, next_hops, algorithm_name
    ="DV")
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


def run_dv_recovery(links, failed_link, baseline_distances,
                    baseline_next_hops, algorithm_name="DV Recovery"):
    """Recover DV routes after a link failure using synchronous updates
    and split horizon with poisoned reverse.
    """
    changed_links = remove_link(links, failed_link)
    adjacency = build_adjacency(changed_links)

    # Preserve the converged routing state.
    distances = {
        node: dict(baseline_distances[node]) for node in NODES
    }
    next_hops = {
        node: dict(baseline_next_hops[node]) for node in NODES
    }

    first, second = failed_link

    # Invalidate routes at the two endpoints that used the failed link.
    for node, failed_neighbor in (
        (first, second),
        (second, first),
    ):
        for destination in NODES:
            if next_hops[node][destination] == failed_neighbor:
                distances[node][destination] = inf
                next_hops[node][destination] = None

    print(f"\n--- {algorithm_name}: {first}-{second} link failure ---")

    update_messages = 0
    rounds = 0
    max_rounds = 100

    while rounds < max_rounds:
        rounds += 1

        # Every router reads the same previous-round state.
        old_distances = {
            node: dict(distances[node]) for node in NODES
        }
        old_next_hops = {
            node: dict(next_hops[node]) for node in NODES
        }

        new_distances = {}
        new_next_hops = {}

        # One distance-vector advertisement per directed link.
        update_messages += sum(
            len(adjacency[node]) for node in NODES
        )

        for node in NODES:
            new_distances[node] = {dest: inf for dest in NODES}
            new_next_hops[node] = {dest: None for dest in NODES}

            # A router's distance to itself is always zero.
            new_distances[node][node] = 0
            new_next_hops[node][node] = node

            for neighbor, link_cost in adjacency[node].items():
                for destination in NODES:
                    # Split horizon with poisoned reverse:
                    # do not advertise a usable route back through
                    # the neighbor from which that route was learned.
                    advertised_cost = old_distances[neighbor][destination]

                    if old_next_hops[neighbor][destination] == node:
                        advertised_cost = inf

                    if advertised_cost == inf:
                        continue

                    candidate_cost = link_cost + advertised_cost

                    if candidate_cost < new_distances[node][destination]:
                        new_distances[node][destination] = candidate_cost
                        new_next_hops[node][destination] = neighbor

        changed = (
            new_distances != old_distances
            or new_next_hops != old_next_hops
        )

        distances = new_distances
        next_hops = new_next_hops

        if not changed:
            break

    if rounds == max_rounds and changed:
        print("WARNING: DV did not converge within the round limit.")

    print(f"Recovery rounds: {rounds}")
    print(f"Distance-vector messages: {update_messages}")

    validate_distances(
        adjacency, distances, algorithm_name
    )

    validate_next_hops(
    adjacency, distances, next_hops, algorithm_name
    )

    print("\nRecovered routing tables:")
    for node in NODES:
        print(f"\nRouter {node}:")
        for destination in NODES:
            print(
                f"  To {destination}: "
                f"cost = {distances[node][destination]}, "
                f"next hop = {next_hops[node][destination]}"
            )

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

    validate_next_hops(
    adjacency, all_distances, all_next_hops, algorithm_name
    ="LS")
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


def run_ls_recovery(links, failed_link, algorithm_name="LS Recovery"):
    """Simulate LS recovery by flooding updated LSAs after a link failure."""

    original_adjacency = build_adjacency(links)
    changed_links = remove_link(links, failed_link)
    changed_adjacency = build_adjacency(changed_links)

    first, second = failed_link

    # Each router starts with the converged LS database.
    lsdb = {
        node: {
            origin: dict(original_adjacency[origin])
            for origin in NODES
        }
        for node in NODES
    }

    # Both endpoints detect the failure and originate updated LSAs.
    updated_lsas = {
        first: dict(changed_adjacency[first]),
        second: dict(changed_adjacency[second]),
    }

    # Install each new LSA at its originating router.
    for origin, lsa in updated_lsas.items():
        lsdb[origin][origin] = dict(lsa)

    # Track which routers have received each changed LSA.
    seen = {
        origin: {origin}
        for origin in updated_lsas
    }

    # Each entry maps an LSA origin to the sender.
    # None means the LSA is being originated locally.
    frontier = {
        origin: {origin: None}
        for origin in updated_lsas
    }

    rounds = 0
    update_messages = 0
    max_rounds = 100

    print(f"\n--- {algorithm_name}: {first}-{second} link failure ---")

    while frontier and rounds < max_rounds:
        rounds += 1
        candidates = {}

        # Flood LSAs synchronously across the changed topology.
        for node, origin_entries in frontier.items():
            for origin, sender in origin_entries.items():
                for neighbor in changed_adjacency[node]:

                    # Do not send the LSA straight back to its sender.
                    if neighbor == sender:
                        continue

                    # Count each transmission attempt.
                    update_messages += 1

                    # A router forwards a changed LSA only once.
                    if neighbor not in seen[origin]:
                        candidates.setdefault(neighbor, {})
                        candidates[neighbor].setdefault(origin, node)

        next_frontier = {}

        # Process received LSAs after the current round ends.
        for node, origin_entries in candidates.items():
            for origin, sender in origin_entries.items():
                if node not in seen[origin]:
                    seen[origin].add(node)
                    lsdb[node][origin] = dict(updated_lsas[origin])

                    next_frontier.setdefault(node, {})
                    next_frontier[node][origin] = sender

        frontier = next_frontier

    if frontier:
        print("WARNING: LS flooding did not finish within the round limit.")

    # Recalculate shortest paths from each router's own LS database.
    distances = {}
    next_hops = {}

    for source in NODES:
        local_graph = {
            origin: dict(neighbors)
            for origin, neighbors in lsdb[source].items()
        }

        source_distances, paths = dijkstra(local_graph, source)

        distances[source] = source_distances
        next_hops[source] = {}

        for destination in NODES:
            path = paths.get(destination, [])

            if destination == source:
                next_hops[source][destination] = source
            elif path:
                next_hops[source][destination] = path[1]
            else:
                next_hops[source][destination] = None

    print(f"Recovery flooding rounds: {rounds}")
    print(f"Changed-LSA transmission attempts: {update_messages}")

    validate_distances(
        changed_adjacency, distances, algorithm_name
    )

    validate_next_hops(
    changed_adjacency, distances, next_hops, algorithm_name
    )

    print("\nRecovered LS routing tables:")

    for node in NODES:
        print(f"\nRouter {node}:")
        for destination in NODES:
            print(
                f"  To {destination}: "
                f"cost = {distances[node][destination]}, "
                f"next hop = {next_hops[node][destination]}"
            )

    return distances, next_hops, rounds, update_messages


# --------------------------------------------------
# 6. RUN THE FOUR BASELINE AND CHANGED-TOPOLOGY TESTS
# --------------------------------------------------


if __name__ == "__main__":
    results = []

    def record_experiment(
        experiment_name, algorithm, topology_links,
        message_type, experiment_result
    ):
        distances, next_hops, rounds, messages = experiment_result
        adjacency = build_adjacency(topology_links)

        distance_ok, next_hop_ok = check_experiment_results(
            adjacency, distances, next_hops
        )

        results.append({
            "experiment": experiment_name,
            "algorithm": algorithm,
            "rounds": rounds,
            "message_count": messages,
            "message_type": message_type,
            "distance_validation": (
                "PASS" if distance_ok else "FAIL"
            ),
            "next_hop_validation": (
                "PASS" if next_hop_ok else "FAIL"
            ),
        })

    dv_message_type = "DV vector advertisement attempts"
    ls_message_type = "LSA transmission attempts"

    # 1. Baseline DV
    print("\n=== Baseline network: DV ===")
    baseline_dv = run_distance_vector(LINKS, "Baseline DV")
    record_experiment(
        "Baseline", "DV", LINKS, dv_message_type, baseline_dv
    )

    # 2. Baseline LS
    print("\n=== Baseline network: LS ===")
    baseline_ls = run_link_state(LINKS, "Baseline LS")
    record_experiment(
        "Baseline", "LS", LINKS, ls_message_type, baseline_ls
    )

    # Remove the B-D link for the failure experiments.
    changed_links = remove_link(LINKS, LINK_CHANGE)

    # 3. DV fresh start after failure
    print("\n=== After B-D failure: DV (fresh start) ===")
    failure_dv = run_distance_vector(
        changed_links, "Failure DV"
    )
    record_experiment(
        "Fresh start after failure",
        "DV", changed_links, dv_message_type, failure_dv
    )

    # 4. LS fresh start after failure
    print("\n=== After B-D failure: LS (fresh start) ===")
    failure_ls = run_link_state(
        changed_links, "Failure LS"
    )
    record_experiment(
        "Fresh start after failure",
        "LS", changed_links, ls_message_type, failure_ls
    )

    # 5. DV recovery using the converged baseline state
    print("\n=== DV recovery after B-D failure ===")
    recovery_dv = run_dv_recovery(
        LINKS,
        LINK_CHANGE,
        baseline_dv[0],
        baseline_dv[1],
        "DV Recovery"
    )
    record_experiment(
        "Recovery after failure",
        "DV", changed_links, dv_message_type, recovery_dv
    )

    # 6. LS recovery after B-D failure
    print("\n=== LS recovery after B-D failure ===")
    recovery_ls = run_ls_recovery(
        LINKS, LINK_CHANGE, "LS Recovery"
    )
    record_experiment(
        "Recovery after failure",
        "LS", changed_links, ls_message_type, recovery_ls
    )

    # Write measurements from this actual run to CSV.
    csv_filename = "results/results.csv"
    fieldnames = [
        "experiment",
        "algorithm",
        "rounds",
        "message_count",
        "message_type",
        "distance_validation",
        "next_hop_validation",
    ]

    with open(
        csv_filename, "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=fieldnames
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to {csv_filename}")
    print("\nValidation summary:")

    for row in results:
        print(
            f"{row['experiment']} | {row['algorithm']} | "
            f"Distances: {row['distance_validation']} | "
            f"Next hops: {row['next_hop_validation']}"
        )

    all_passed = all(
        row["distance_validation"] == "PASS"
        and row["next_hop_validation"] == "PASS"
        for row in results
    )

    print(
        "\nOverall validation:",
        "PASS" if all_passed else "FAIL"
    )
