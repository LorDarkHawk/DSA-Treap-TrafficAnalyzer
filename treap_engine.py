class TreapNode:
    def __init__(self, timestamp, priority, vehicle_id, data=None):
        self.timestamp = timestamp       # BST Key: Arrival time 
        self.priority = priority         # Max-Heap Key: Emergency level (Higher = more critical)
        self.vehicle_id = vehicle_id     
        self.data = data                 
        self.left = None
        self.right = None

class TrafficTreap:
    def __init__(self):
        self.root = None

    # O(1) Pointer swaps for balancing
    def _right_rotate(self, y):
        x = y.left
        y.left = x.right
        x.right = y
        return x

    def _left_rotate(self, x):
        y = x.right
        x.right = y.left
        y.left = x
        return y

    def insert(self, timestamp, priority, vehicle_id, data=None):
        """Public method to insert a new traffic event."""
        self.root = self._insert_rec(self.root, timestamp, priority, vehicle_id, data)

    def _insert_rec(self, root, timestamp, priority, vehicle_id, data):
        # 1. Standard BST insertion based on timestamp
        if not root:
            return TreapNode(timestamp, priority, vehicle_id, data)

        if timestamp < root.timestamp:
            root.left = self._insert_rec(root.left, timestamp, priority, vehicle_id, data)
            # 2. Maintain Max-Heap property: Rotate right if child priority is higher
            if root.left and root.left.priority > root.priority:
                root = self._right_rotate(root)
        elif timestamp > root.timestamp:
            root.right = self._insert_rec(root.right, timestamp, priority, vehicle_id, data)
            # 2. Maintain Max-Heap property: Rotate left if child priority is higher
            if root.right and root.right.priority > root.priority:
                root = self._left_rotate(root)
        else:
            # EDGE CASE HANDLING: Duplicate timestamp collision
            # We append a microsecond differentiator to avoid overwriting data
            return self._insert_rec(root, timestamp + 0.0001, priority, vehicle_id, data)

        return root

    def delete(self, timestamp):
        """Public method to remove a traffic event once processed."""
        self.root = self._delete_rec(self.root, timestamp)

    def _delete_rec(self, root, timestamp):
        if not root:
            return None

        # Search for the node by timestamp
        if timestamp < root.timestamp:
            root.left = self._delete_rec(root.left, timestamp)
        elif timestamp > root.timestamp:
            root.right = self._delete_rec(root.right, timestamp)
        else:
            # Node found. Now push it down to a leaf position using rotations
            if not root.left and not root.right:
                return None
            elif not root.left:
                root = self._left_rotate(root)
                root.left = self._delete_rec(root.left, timestamp)
            elif not root.right:
                root = self._right_rotate(root)
                root.right = self._delete_rec(root.right, timestamp)
            # Both children exist: rotate the child with the higher priority up
            elif root.left.priority > root.right.priority:
                root = self._right_rotate(root)
                root.right = self._delete_rec(root.right, timestamp)
            else:
                root = self._left_rotate(root)
                root.left = self._delete_rec(root.left, timestamp)

        return root

    def range_query(self, start_time, end_time):
        """Fetches all events in a specific time window in O(log n + k) time."""
        result = []
        self._range_query_rec(self.root, start_time, end_time, result)
        return result

    def _range_query_rec(self, root, start_time, end_time, result):
        if not root:
            return
        
        if root.timestamp > start_time:
            self._range_query_rec(root.left, start_time, end_time, result)
            
        if start_time <= root.timestamp <= end_time:
            result.append({
                "timestamp": root.timestamp,
                "priority": root.priority,
                "vehicle_id": root.vehicle_id,
                "data": root.data
            })
            
        if root.timestamp < end_time:
            self._range_query_rec(root.right, start_time, end_time, result)
    def search(self, timestamp):
        """Finds a specific traffic event by its exact arrival time in O(log n) time."""
        return self._search_rec(self.root, timestamp)

    def _search_rec(self, root, timestamp):
        if not root:
            return None
        
        # If found, return a dictionary of the vehicle's data
        if root.timestamp == timestamp:
            return {
                "timestamp": root.timestamp,
                "priority": root.priority,
                "vehicle_id": root.vehicle_id,
                "data": root.data
            }
        elif timestamp < root.timestamp:
            return self._search_rec(root.left, timestamp)
        else:
            return self._search_rec(root.right, timestamp)

    def correct(self, timestamp, new_priority, new_vehicle_id, new_data):
        """
        Updates an existing traffic event. 
        Because changing priority breaks the Max-Heap property, the mathematically 
        safest O(log n) approach is to delete the old node and insert the corrected one.
        """
        existing_record = self.search(timestamp)
        
        if existing_record:
            # Remove the outdated record
            self.delete(timestamp)
            # Insert the fresh record with updated data/priority
            self.insert(timestamp, new_priority, new_vehicle_id, new_data)
            return True
        else:
            print(f"Error: No vehicle found at timestamp {timestamp} to correct.")
            return False
