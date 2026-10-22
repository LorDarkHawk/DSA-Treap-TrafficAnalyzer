import random
import time
import os
from treap_engine import TrafficTreap


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def show_dashboard(vehicles, message):
    clear_screen()
    print("=" * 60)
    print("          TRAFFIC PRIORITY TIMESTAMP SYSTEM")
    print("=" * 60)
    print(message)
    print("-" * 60)
    print("VEHICLE ID   TIMESTAMP   TYPE          PRIORITY")
    print("-" * 60)

    for vehicle in sorted(vehicles, key=lambda item: item["timestamp"]):
        print(
            vehicle["vehicle_id"], "       ",
            vehicle["timestamp"], "   ",
            vehicle["data"]["type"], "   ",
            vehicle["priority"]
        )

    print("=" * 60)


def main():
    treap = TrafficTreap()
    vehicles = []

    # Generate and insert 18 vehicles
    for i in range(1, 19):
        timestamp = random.randint(100, 999)

        # Make timestamps unique
        while any(vehicle["timestamp"] == timestamp for vehicle in vehicles):
            timestamp = random.randint(100, 999)

        if i == 3 or i == 11:
            vehicle_type = "Ambulance"
            priority = 10
        elif i == 7:
            vehicle_type = "Fire Truck"
            priority = 9
        else:
            vehicle_type = "Regular"
            priority = 1

        vehicle = {
            "timestamp": timestamp,
            "priority": priority,
            "vehicle_id": "V" + str(i),
            "data": {"type": vehicle_type}
        }

        treap.insert(timestamp, priority, vehicle["vehicle_id"], vehicle["data"])
        vehicles.append(vehicle)

        show_dashboard(vehicles, "Inserted " + vehicle["vehicle_id"])
        time.sleep(0.5)

    # Perform a range query
    start_time = 300
    end_time = 700
    result = treap.range_query(start_time, end_time)

    show_dashboard(vehicles, "Range query: " + str(start_time) + " to " + str(end_time))
    print("\nVehicles found in range:")
    for vehicle in result:
        print(vehicle)
    if not result:
        print("No vehicles found in this range.")

    input("\nPress Enter to continue to deletion...")

    # Delete one vehicle
    vehicle = vehicles[0]
    treap.delete(vehicle["timestamp"])
    vehicles.remove(vehicle)

    show_dashboard(vehicles, "Deleted " + vehicle["vehicle_id"])
    print("\nSimulation completed.")
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
