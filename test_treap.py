
import random
from treap_engine import TrafficTreap


passed = 0
failed = 0
warnings = 0


def check(name, condition, detail=""):
    """Print a PASS/FAIL result and update totals."""
    global passed, failed
    if condition:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" — {detail}" if detail else ""))


def warn(name, detail):
    """Report a limitation that cannot be tested with the current engine."""
    global warnings
    warnings += 1
    print(f"WARN: {name} — {detail}")


def is_valid(node, low=float("-inf"), high=float("inf")):
    """Validate strict BST ordering and max-heap priority ordering."""
    if node is None:
        return True

    if not (low < node.timestamp < high):
        return False

    if node.left is not None and node.left.priority > node.priority:
        return False

    if node.right is not None and node.right.priority > node.priority:
        return False

    return (
        is_valid(node.left, low, node.timestamp)
        and is_valid(node.right, node.timestamp, high)
    )


def height(node):
    """Return tree height measured in nodes; empty tree has height 0."""
    if node is None:
        return 0
    return 1 + max(height(node.left), height(node.right))


def events_between(tree, low, high):
    """Return range-query results, preserving the engine's returned records."""
    return tree.range_query(low, high)


def timestamps_between(tree, low, high):
    return [event["timestamp"] for event in events_between(tree, low, high)]


def all_events(tree):
    """Collect all events across the timestamp range used by this test suite."""
    return tree.range_query(float("-inf"), float("inf"))


def make_tree(rows):
    tree = TrafficTreap()
    for timestamp, priority, vehicle_id in rows:
        tree.insert(timestamp, priority, vehicle_id)
    return tree


def test_basic_operations():
    print("\n=== Basic operations and invariants ===")
    tree = make_tree([
        (50, 3, "CAR1"),
        (20, 7, "AMBULANCE"),
        (70, 1, "CAR2"),
    ])

    check("Three events can be inserted", len(all_events(tree)) == 3)
    check("BST and max-heap invariants hold", is_valid(tree.root))
    check("Root is the highest-priority event",
          tree.root.timestamp == 20 and tree.root.priority == 7)
    check("Height matches the current three-node tree", height(tree.root) == 3)
    check("Range query returns sorted timestamps",
          timestamps_between(tree, 0, 100) == [20, 50, 70])
    check("Range query includes both interval endpoints",
          timestamps_between(tree, 20, 50) == [20, 50])

    tree.delete(50)
    check("Deleted event is absent",
          all(event["timestamp"] != 50 for event in all_events(tree)))
    check("Tree remains valid after deletion", is_valid(tree.root))


def test_duplicate_timestamps():
    print("\n=== Duplicate timestamp policy ===")
    tree = TrafficTreap()
    tree.insert(50, 3, "CAR1")
    tree.insert(50, 5, "CAR2")

    events = all_events(tree)
    timestamps = [event["timestamp"] for event in events]
    vehicle_ids = [event["vehicle_id"] for event in events]

    check("Both events survive duplicate insertion", len(events) == 2)
    check("Second timestamp is shifted by 0.0001",
          50 in timestamps and 50.0001 in timestamps)
    check("Both vehicle IDs are preserved",
          "CAR1" in vehicle_ids and "CAR2" in vehicle_ids)
    check("Tree remains valid after duplicate insertion", is_valid(tree.root))

    # Demonstrate a limitation: querying exactly [50, 50] won't return
    # the event shifted to 50.0001.
    exact_timestamp_events = tree.range_query(50, 50)
    check("Exact timestamp query returns only the original timestamp",
          len(exact_timestamp_events) == 1
          and exact_timestamp_events[0]["vehicle_id"] == "CAR1")


def test_deletion_edge_cases():
    print("\n=== Deletion edge cases ===")
    tree = make_tree([
        (50, 10, "ROOT"),
        (30, 5, "LEFT"),
        (70, 4, "RIGHT"),
        (20, 2, "LEAF"),
        (40, 3, "TWO_CHILD_CANDIDATE"),
    ])

    root_timestamp = tree.root.timestamp
    tree.delete(root_timestamp)
    check("Deleting root removes the root event",
          all(event["timestamp"] != root_timestamp for event in all_events(tree)))
    check("Tree remains valid after root deletion", is_valid(tree.root))

    tree.delete(20)
    check("Deleting leaf removes the leaf event",
          all(event["timestamp"] != 20 for event in all_events(tree)))
    check("Tree remains valid after leaf deletion", is_valid(tree.root))

    # The node at 30 has children 20 and 40 in this constructed tree, but
    # 20 was just deleted. Build a fresh tree to test deleting a two-child node.
    two_child_tree = make_tree([
        (50, 10, "ROOT"),
        (30, 5, "NODE"),
        (70, 4, "RIGHT"),
        (20, 2, "LEFT_LEAF"),
        (40, 3, "RIGHT_LEAF"),
    ])
    two_child_tree.delete(30)
    check("Deleting a node with two children removes it",
          all(event["timestamp"] != 30 for event in all_events(two_child_tree)))
    check("Tree remains valid after two-child deletion",
          is_valid(two_child_tree.root))

    before = [(e["timestamp"], e["vehicle_id"]) for e in all_events(tree)]
    tree.delete(999)
    after = [(e["timestamp"], e["vehicle_id"]) for e in all_events(tree)]
    check("Deleting a missing timestamp leaves events unchanged",
          before == after)
    check("Deleting a missing timestamp leaves tree valid",
          is_valid(tree.root))


def test_range_edges():
    print("\n=== Range-query edge cases ===")
    tree = make_tree([
        (20, 7, "A"),
        (50, 3, "B"),
        (70, 1, "C"),
    ])

    check("Range with no matching events is empty",
          tree.range_query(100, 200) == [])
    check("Inverted range is empty", tree.range_query(80, 30) == [])
    check("Full range returns all events",
          timestamps_between(tree, float("-inf"), float("inf")) == [20, 50, 70])
    check("Empty tree range query returns empty",
          TrafficTreap().range_query(0, 100) == [])
    check("Range below all events is empty", tree.range_query(-10, 10) == [])
    check("Range above all events is empty", tree.range_query(80, 100) == [])


def test_empty_tree_and_capabilities():
    print("\n=== Empty tree and API capabilities ===")
    empty = TrafficTreap()
    check("New tree has no root", empty.root is None)
    check("Empty tree is valid", is_valid(empty.root))
    check("Empty tree height is zero", height(empty.root) == 0)
    check("Deleting from empty tree leaves it empty",
          (empty.delete(123) is None) and empty.root is None)

    if callable(getattr(empty, "search", None)):
        warn("Search API exists",
             "Add dedicated search tests based on its documented return format.")
    else:
        warn("Search operation",
             "TrafficTreap has no public search() method; cannot test searching.")

    if callable(getattr(empty, "correct", None)):
        warn("Correction API exists",
             "Add correction tests based on its documented arguments.")
    else:
        warn("Correction operation",
             "TrafficTreap has no public correct() method; cannot test corrections.")


def test_stress_insertions():
    print("\n=== Stress tests ===")
    rng = random.Random(20261022)

    # Distinct random timestamps; priorities match the current engine's
    # max-heap rule. Repeated timestamps are tested separately.
    random_rows = [
        (timestamp, rng.randint(1, 1_000_000), f"R{timestamp}")
        for timestamp in rng.sample(range(1, 1_000_000), 1000)
    ]
    random_tree = TrafficTreap()
    random_ok = True
    for timestamp, priority, vehicle_id in random_rows:
        random_tree.insert(timestamp, priority, vehicle_id)
        if not is_valid(random_tree.root):
            random_ok = False
            break

    check("1000 random insertions preserve invariants", random_ok)
    check("Random stress tree contains all 1000 events",
          len(all_events(random_tree)) == 1000)
    print(f"INFO: Random-input tree height = {height(random_tree.root)}")

    # Sorted timestamps test. This does not guarantee balance because this
    # implementation uses event severity as priority, not randomized priority.
    sorted_tree = TrafficTreap()
    sorted_ok = True
    for timestamp in range(1, 1001):
        sorted_tree.insert(timestamp, rng.randint(1, 1_000_000), f"S{timestamp}")
        if not is_valid(sorted_tree.root):
            sorted_ok = False
            break

    check("1000 sorted-timestamp insertions preserve invariants", sorted_ok)
    check("Sorted stress tree contains all 1000 events",
          len(all_events(sorted_tree)) == 1000)
    print(f"INFO: Sorted-input tree height = {height(sorted_tree.root)}")


def test_random_mixed_operations():
    print("\n=== Random mixed-operation reference test ===")
    rng = random.Random(314159)
    tree = TrafficTreap()
    reference = {}  # timestamp -> (priority, vehicle_id)
    next_timestamp = 1
    consistent = True

    # Use unique timestamps so this test does not depend on the engine's
    # duplicate timestamp shifting policy.
    for operation_number in range(1000):
        should_insert = not reference or rng.random() < 0.60

        if should_insert:
            timestamp = next_timestamp
            next_timestamp += 1
            priority = rng.randint(1, 10000)
            vehicle_id = f"M{timestamp}"
            tree.insert(timestamp, priority, vehicle_id)
            reference[timestamp] = (priority, vehicle_id)
        else:
            timestamp = rng.choice(list(reference.keys()))
            tree.delete(timestamp)
            del reference[timestamp]

        if not is_valid(tree.root):
            consistent = False
            break

        actual = {
            event["timestamp"]: (event["priority"], event["vehicle_id"])
            for event in all_events(tree)
        }
        if actual != reference:
            consistent = False
            break

    check("1000 mixed insert/delete operations match reference model",
          consistent)
    check("Final mixed-operation tree satisfies invariants",
          is_valid(tree.root))
    print(f"INFO: Mixed-operation final event count = {len(all_events(tree))}")
    print(f"INFO: Mixed-operation final tree height = {height(tree.root)}")


def main():
    print("=" * 64)
    print("ROLE 3 — TREAP TEST SUITE")
    print("=" * 64)

    test_basic_operations()
    test_duplicate_timestamps()
    test_deletion_edge_cases()
    test_range_edges()
    test_empty_tree_and_capabilities()
    test_stress_insertions()
    test_random_mixed_operations()

    print("\n" + "=" * 64)
    print(f"FINAL RESULTS: {passed} passed, {failed} failed, {warnings} warning(s)")
    print("=" * 64)

    if failed:
        print("Some tests failed. Report the failing case to Role 1.")
    else:
        print("All executable tests passed.")
    if warnings:
        print("Warnings identify API features absent from the current engine.")
    print("Note: passing tests do not prove expected O(log n) performance.")


if __name__ == "__main__":
    main()
