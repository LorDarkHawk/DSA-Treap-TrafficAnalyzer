
from treap_engine import TrafficTreap


def is_valid(node, low=float("-inf"), high=float("inf")):
    if node is None:
        return True

    if not low < node.timestamp < high:
        return False

    if node.left and node.left.priority > node.priority:
        return False
    if node.right and node.right.priority > node.priority:
        return False

    return (
        is_valid(node.left, low, node.timestamp)
        and is_valid(node.right, node.timestamp, high)
    )


def show_events(tree, start, end):
    events = tree.range_query(start, end)

    print(f"\nEvents between {start} and {end}:")
    for event in events:
        print(event)

    if not events:
        print("No events found.")


def main():
    tree = TrafficTreap()

    print("=== DEMO 1: INSERT AND RANGE QUERY ===")
    tree.insert(50, 3, "CAR1")
    tree.insert(20, 7, "AMBULANCE")
    tree.insert(70, 1, "CAR2")

    show_events(tree, 0, 100)
    print("Treap valid:", is_valid(tree.root))

    print("\n=== DEMO 2: DUPLICATE TIMESTAMP ===")
    tree.insert(50, 5, "CAR3")

    show_events(tree, 50, 50.0001)
    print("Treap valid:", is_valid(tree.root))

    print("\n=== DEMO 3: DELETE AN EVENT ===")
    tree.delete(50)

    show_events(tree, 0, 100)
    print("Treap valid after deletion:", is_valid(tree.root))

    print("\n=== DEMO 4: EMPTY RANGE ===")
    show_events(tree, 200, 300)

    print("\n=== LIVE DEMO COMPLETE ===")


if __name__ == "__main__":
    main()
