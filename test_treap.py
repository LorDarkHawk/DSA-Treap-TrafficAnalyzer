import random
from treap_engine import TrafficTreap


passed = 0
failed = 0
warnings = 0


# --------------------------------------------------
# TEST RUNNER
# --------------------------------------------------

def check(name, condition, detail=""):
    """Print PASS/FAIL and update test counters."""
    global passed, failed

    if condition:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" — {detail}" if detail else ""))


def warn(name, detail):
    """Report a limitation separately from failed tests."""
    global warnings
    warnings += 1
    print(f"WARN: {name} — {detail}")


# --------------------------------------------------
# TREAP VALIDATION
# --------------------------------------------------

def is_valid(node, low=float("-inf"), high=float("inf")):
    """Check strict BST ordering and max-heap priority ordering."""

    if node is None:
        return True

    # Check BST timestamp boundaries
    if not (low < node.timestamp < high):
        return False

    # Check max-heap property for left child
    if node.left is not None and node.left.priority > node.priority:
        return False

    # Check max-heap property for right child
    if node.right is not None and node.right.priority > node.priority:
        return False

    # Recursively validate both subtrees
    return (
        is_valid(node.left, low, node.timestamp)
        and is_valid(node.right, node.timestamp, high)
    )


def height(node):
    """Return tree height measured in nodes. Empty tree has height 0."""

    if node is None:
        return 0

    return 1 + max(height(node.left), height(node.right))


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def events_between(tree, low, high):
    """Return events in a timestamp range."""
    return tree.range_query(low, high)


def timestamps_between(tree, low, high):
    """Return timestamps from a range query."""
    return [
        event["timestamp"]
        for event in events_between(tree, low, high)
    ]


def all_events(tree):
    """Return all events stored in the tree."""
    return tree.range_query(float("-inf"), float("inf"))


def make_tree(rows):
    """Create a Treap from (timestamp, priority, vehicle_id) tuples."""

    tree = TrafficTreap()

    for timestamp, priority, vehicle_id in rows:
        tree.insert(timestamp, priority, vehicle_id)

    return tree


# --------------------------------------------------
# TEST 1: BASIC OPERATIONS
# --------------------------------------------------

def test_basic_operations():
    print("\n=== Basic operations and invariants ===")

    tree = make_tree([
        (50, 3, "CAR1"),
        (20, 7, "AMBULANCE"),
        (70, 1, "CAR2"),
    ])

    check(
        "Three events can be inserted",
        len(all_events(tree)) == 3
    )

    check(
        "BST and max-heap invariants hold",
        is_valid(tree.root)
    )

    check(
        "Root is the highest-priority event",
        tree.root.timestamp == 20 and tree.root.priority == 7
    )

    check(
        "Height matches the current three-node tree",
        height(tree.root) == 3
    )

    check(
        "Range query returns sorted timestamps",
        timestamps_between(tree, 0, 100) == [20, 50, 70]
    )

    check(
        "Range query includes both endpoints",
        timestamps_between(tree, 20, 50) == [20, 50]
    )

    tree.delete(50)

    check(
        "Deleted event is absent",
        all(event["timestamp"] != 50 for event in all_events(tree))
    )

    check(
        "Tree remains valid after deletion",
        is_valid(tree.root)
    )


# --------------------------------------------------
# TEST 2: DUPLICATE TIMESTAMPS
# --------------------------------------------------

def test_duplicate_timestamps():
    print("\n=== Duplicate timestamp policy ===")

    tree = TrafficTreap()

    tree.insert(50, 3, "CAR1")
    tree.insert(50, 5, "CAR2")

    events = all_events(tree)

    timestamps = [event["timestamp"] for event in events]
    vehicle_ids = [event["vehicle_id"] for event in events]

    check(
        "Both events survive duplicate insertion",
        len(events) == 2
    )

    check(
        "Second timestamp is shifted by 0.0001",
        50 in timestamps and 50.0001 in timestamps
    )

    check(
        "Both vehicle IDs are preserved",
        "CAR1" in vehicle_ids and "CAR2" in vehicle_ids
    )

    check(
        "Tree remains valid after duplicate insertion",
        is_valid(tree.root)
    )

    # The second event has a shifted timestamp.
    exact_timestamp_events = tree.range_query(50, 50)

    check(
        "Exact timestamp query returns only the original event",
        len(exact_timestamp_events) == 1
        and exact_timestamp_events[0]["vehicle_id"] == "CAR1"
    )


# --------------------------------------------------
# TEST 3: SEARCH OPERATION
# --------------------------------------------------

def test_search():
    print("\n=== Search operation ===")

    tree = make_tree([
        (10, 5, "CAR1"),
        (20, 9, "AMBULANCE"),
        (30, 3, "CAR2"),
    ])

    # Search for an existing event
    result = tree.search(20)

    check(
        "Search finds an existing event",
        result is not None
        and result["timestamp"] == 20
        and result["vehicle_id"] == "AMBULANCE"
    )

    check(
        "Search returns the correct priority",
        result is not None and result["priority"] == 9
    )

    # Search for a nonexistent event
    missing = tree.search(999)

    check(
        "Search returns None for a missing timestamp",
        missing is None
    )

    # Search in an empty tree
    empty = TrafficTreap()

    check(
        "Search in an empty tree returns None",
        empty.search(10) is None
    )


# --------------------------------------------------
# TEST 4: CORRECTION OPERATION
# --------------------------------------------------

def test_correction():
    print("\n=== Correction operation ===")

    tree = make_tree([
        (10, 5, "CAR1"),
        (20, 9, "AMBULANCE"),
        (30, 3, "CAR2"),
    ])

    # Correct the event at timestamp 10
    corrected = tree.correct(
        10,
        8,
        "CAR1_UPDATED",
        {"speed": 40}
    )

    result = tree.search(10)

    check(
        "Correction succeeds for an existing event",
        corrected is True
    )

    check(
        "Correction updates priority",
        result is not None and result["priority"] == 8
    )

    check(
        "Correction updates vehicle ID",
        result is not None and result["vehicle_id"] == "CAR1_UPDATED"
    )

    check(
        "Correction updates additional data",
        result is not None and result["data"] == {"speed": 40}
    )

    check(
        "Correction preserves the number of events",
        len(all_events(tree)) == 3
    )

    check(
        "Tree remains valid after correction",
        is_valid(tree.root)
    )

    # Attempt to correct a missing timestamp
    missing_correction = tree.correct(
        999,
        5,
        "UNKNOWN",
        None
    )

    check(
        "Correction returns False for a missing event",
        missing_correction is False
    )

    check(
        "Tree remains valid after unsuccessful correction",
        is_valid(tree.root)
    )


# --------------------------------------------------
# TEST 5: DELETION EDGE CASES
# --------------------------------------------------

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

    check(
        "Deleting root removes the root event",
        all(
            event["timestamp"] != root_timestamp
            for event in all_events(tree)
        )
    )

    check(
        "Tree remains valid after root deletion",
        is_valid(tree.root)
    )

    tree.delete(20)

    check(
        "Deleting leaf removes the leaf event",
        all(
            event["timestamp"] != 20
            for event in all_events(tree)
        )
    )

    check(
        "Tree remains valid after leaf deletion",
        is_valid(tree.root)
    )

    # Build a fresh tree to test deleting a node with two children.
    two_child_tree = make_tree([
        (50, 10, "ROOT"),
        (30, 5, "NODE"),
        (70, 4, "RIGHT"),
        (20, 2, "LEFT_LEAF"),
        (40, 3, "RIGHT_LEAF"),
    ])

    two_child_tree.delete(30)

    check(
        "Deleting a node with two children removes it",
        all(
            event["timestamp"] != 30
            for event in all_events(two_child_tree)
        )
    )

    check(
        "Tree remains valid after two-child deletion",
        is_valid(two_child_tree.root)
    )

    # Check deletion of a nonexistent timestamp.
    before = [
        (event["timestamp"], event["vehicle_id"])
        for event in all_events(tree)
    ]

    tree.delete(999)

    after = [
        (event["timestamp"], event["vehicle_id"])
        for event in all_events(tree)
    ]

    check(
        "Deleting a missing timestamp leaves events unchanged",
        before == after
    )

    check(
        "Deleting a missing timestamp leaves tree valid",
        is_valid(tree.root)
    )


# --------------------------------------------------
# TEST 6: RANGE QUERY EDGE CASES
# --------------------------------------------------

def test_range_edges():
    print("\n=== Range-query edge cases ===")

    tree = make_tree([
        (20, 7, "A"),
        (50, 3, "B"),
        (70, 1, "C"),
    ])

    check(
        "Range with no matching events is empty",
        tree.range_query(100, 200) == []
    )

    check(
        "Inverted range is empty",
        tree.range_query(80, 30) == []
    )

    check(
        "Full range returns all events",
        timestamps_between(
            tree, float("-inf"), float("inf")
        ) == [20, 50, 70]
    )

    check(
        "Empty tree range query returns empty",
        TrafficTreap().range_query(0, 100) == []
    )

    check(
        "Range below all events is empty",
        tree.range_query(-10, 10) == []
    )

    check(
        "Range above all events is empty",
        tree.range_query(80, 100) == []
    )


# --------------------------------------------------
# TEST 7: EMPTY TREE
# --------------------------------------------------

def test_empty_tree():
    print("\n=== Empty tree ===")

    empty = TrafficTreap()

    check(
        "New tree has no root",
        empty.root is None
    )

    check(
        "Empty tree is valid",
        is_valid(empty.root)
    )

    check(
        "Empty tree height is zero",
        height(empty.root) == 0
    )

    empty.delete(123)

    check(
        "Deleting from empty tree leaves it empty",
        empty.root is None
    )

    check(
        "Empty tree remains valid after deletion",
        is_valid(empty.root)
    )


# --------------------------------------------------
# TEST 8: STRESS INSERTIONS
# --------------------------------------------------

def test_stress_insertions():
    print("\n=== Stress tests ===")

    rng = random.Random(20261022)

    # Random distinct timestamps
    random_rows = [
        (
            timestamp,
            rng.randint(1, 1_000_000),
            f"R{timestamp}"
        )
        for timestamp in rng.sample(range(1, 1_000_000), 1000)
    ]

    random_tree = TrafficTreap()
    random_ok = True

    for timestamp, priority, vehicle_id in random_rows:
        random_tree.insert(timestamp, priority, vehicle_id)

        if not is_valid(random_tree.root):
            random_ok = False
            break

    check(
        "1000 random insertions preserve invariants",
        random_ok
    )

    check(
        "Random stress tree contains all 1000 events",
        len(all_events(random_tree)) == 1000
    )

    print(
        f"INFO: Random-input tree height = "
        f"{height(random_tree.root)}"
    )

    # Sorted timestamps
    sorted_tree = TrafficTreap()
    sorted_ok = True

    for timestamp in range(1, 1001):
        priority = rng.randint(1, 1_000_000)

        sorted_tree.insert(
            timestamp,
            priority,
            f"S{timestamp}"
        )

        if not is_valid(sorted_tree.root):
            sorted_ok = False
            break

    check(
        "1000 sorted-timestamp insertions preserve invariants",
        sorted_ok
    )

    check(
        "Sorted stress tree contains all 1000 events",
        len(all_events(sorted_tree)) == 1000
    )

    print(
        f"INFO: Sorted-input tree height = "
        f"{height(sorted_tree.root)}"
    )


# --------------------------------------------------
# TEST 9: RANDOM MIXED OPERATIONS
# --------------------------------------------------

def test_random_mixed_operations():
    print("\n=== Random mixed-operation reference test ===")

    rng = random.Random(314159)

    tree = TrafficTreap()

    # Reference model: timestamp -> (priority, vehicle_id)
    reference = {}

    next_timestamp = 1
    consistent = True

    for operation_number in range(1000):

        should_insert = (
            not reference or rng.random() < 0.60
        )

        if should_insert:
            timestamp = next_timestamp
            next_timestamp += 1

            priority = rng.randint(1, 10000)
            vehicle_id = f"M{timestamp}"

            tree.insert(timestamp, priority, vehicle_id)

            reference[timestamp] = (
                priority,
                vehicle_id
            )

        else:
            timestamp = rng.choice(list(reference.keys()))

            tree.delete(timestamp)
            del reference[timestamp]

        # Validate tree invariants after each operation.
        if not is_valid(tree.root):
            consistent = False
            break

        # Compare actual tree contents with the reference model.
        actual = {
            event["timestamp"]: (
                event["priority"],
                event["vehicle_id"]
            )
            for event in all_events(tree)
        }

        if actual != reference:
            consistent = False
            break

    check(
        "1000 mixed insert/delete operations match reference model",
        consistent
    )

    check(
        "Final mixed-operation tree satisfies invariants",
        is_valid(tree.root)
    )

    print(
        f"INFO: Mixed-operation final event count = "
        f"{len(all_events(tree))}"
    )

    print(
        f"INFO: Mixed-operation final tree height = "
        f"{height(tree.root)}"
    )


# --------------------------------------------------
# MAIN TEST RUNNER
# --------------------------------------------------

def main():
    print("=" * 64)
    print("ROLE 3 — TREAP TEST SUITE")
    print("=" * 64)

    test_basic_operations()
    test_duplicate_timestamps()
    test_search()
    test_correction()
    test_deletion_edge_cases()
    test_range_edges()
    test_empty_tree()
    test_stress_insertions()
    test_random_mixed_operations()

    print("\n" + "=" * 64)
    print(
        f"FINAL RESULTS: {passed} passed, "
        f"{failed} failed, {warnings} warning(s)"
    )
    print("=" * 64)

    if failed:
        print("Some tests failed. Investigate the failing cases.")
    else:
        print("All executable tests passed.")

    if warnings:
        print("Warnings identify limitations that require attention.")

    print(
        "Note: passing tests do not prove expected O(log n) performance."
    )


if __name__ == "__main__":
    main()
