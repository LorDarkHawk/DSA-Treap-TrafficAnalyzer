# Traffic Priority Timestamp System

A traffic-event manager built on a **Treap**: a Binary Search Tree ordered by **timestamp** that is simultaneously a **Max-Heap** ordered by **emergency priority**.

It lets a traffic control room do three things efficiently:

1. Log events as they arrive (**Insert**)
2. Remove resolved or cancelled events (**Delete**)
3. Pull every event in a time window, e.g. "all incidents between 08:00 and 09:30" (**Range Query**)

while always keeping the **most urgent event** available at the root in O(1).

---

## Table of Contents

1. [Data Structure Overview](#1-data-structure-overview)
2. [Data Structure Justification](#2-data-structure-justification)
3. [Time Complexity Analysis](#3-time-complexity-analysis)
4. [Why the Randomized Heap Invariant Gives Expected O(log n)](#4-why-the-randomized-heap-invariant-gives-expected-olog-n)
5. [Algorithms (Pseudocode)](#5-algorithms-pseudocode)
6. [Team](#6-team)

---

## 1. Data Structure Overview

Each node stores:

| Field | Role |
|---|---|
| `timestamp` | **BST key.** Left subtree has smaller timestamps, right subtree has larger. |
| `emergency` | Emergency level of the event (higher = more urgent). |
| `rand` | A random tiebreaker, drawn once at insertion. |
| `left`, `right` | Child pointers. |

The **heap priority** of a node is the pair `(emergency, rand)`, compared lexicographically. The treap maintains two invariants at all times:

* **BST invariant (on `timestamp`):** `left.timestamp < node.timestamp < right.timestamp`
* **Max-Heap invariant (on priority):** `node.priority >= left.priority` and `node.priority >= right.priority`

Consequences:

* The **root** is always the most urgent event in the whole system, so `peekMostUrgent()` is O(1).
* An **in-order traversal** yields events in chronological order.
* For a fixed set of distinct priorities, the treap shape is **unique and independent of insertion order**. This is the property that the expected-time proof relies on.

> **Assumption:** timestamps are unique. If two events can share a timestamp, break ties with a sequence number so keys stay distinct.

---

## 2. Data Structure Justification

### The problem needs two things at once

| Requirement | Meaning |
|---|---|
| **Time-ordered access** | Insert, delete and *range query* by timestamp |
| **Priority-ordered access** | Instantly know the most urgent event |

No single classical structure gives both cleanly. A Treap does.

### Treap vs. Max-Heap

A binary heap only enforces a *parent-versus-child* order. There is **no ordering between siblings or across subtrees**, so a heap carries no information about timestamps.

* **Range query by timestamp:** the heap cannot prune any branch. Every node might lie inside the window, so the only option is a full scan, **O(n)**, regardless of how few events match.
* **Delete an arbitrary event:** locating it by timestamp is also a scan, **O(n)** (unless we bolt on a separate hash index, which adds extra memory and synchronization).
* **Chronological listing:** requires sorting, **O(n log n)**.

The Treap keeps the heap's strength (max-priority at the root) and adds BST ordering, so a range query prunes whole subtrees and costs **O(log n + k)**.

### Treap vs. AVL Tree

An AVL tree is a perfectly good ordered structure, but it fits this workload less well:

* **It has no notion of emergency priority.** An AVL tree orders by one key only. Getting the most urgent event would need an extra augmentation (a subtree-max field) that must be recomputed on every insertion, deletion and rotation. In a Treap, the most urgent event is the root *by construction*.
* **Rebalancing cost and bookkeeping.** AVL stores a height or balance factor in every node and retraces the path to the root after each update. A single AVL *deletion* can trigger **up to O(log n) rotations**. In a Treap, the **expected number of rotations per insert or delete is a constant (< 2)**, which matters for a high-throughput stream of events.
* **Simplicity.** A Treap needs only one rotation routine and one comparison. There are no four rebalancing cases (LL, LR, RR, RL).

> **Honest trade-off:** AVL gives a *deterministic* O(log n) worst case and slightly shallower trees (height at most about 1.44 log2 n). A Treap gives O(log n) in *expectation*, with a tiny probability of a bad shape. For a system that must also expose "most urgent event" for free, the expected-case guarantee is a good trade.

### Summary

| Criterion | Max-Heap | AVL Tree | **Treap** |
|---|---|---|---|
| Most urgent event | O(1) | Needs augmentation | **O(1) (root)** |
| Search / delete by timestamp | O(n) | O(log n) | **O(log n) expected** |
| Range query by timestamp | **O(n)** | O(log n + k) | **O(log n + k) expected** |
| Rotations per update | n/a | Up to O(log n) on delete | **Expected O(1) (< 2)** |
| Extra balance data per node | None | Height / balance factor | **None** (one priority) |
| Implementation complexity | Low | High (4 cases) | **Low-moderate** |

---

## 3. Time Complexity Analysis

`n` = number of events stored, `k` = number of events reported by a range query.

| Operation | Expected | Worst Case | Notes |
|---|---|---|---|
| **Insert** | **O(log n)** | O(n) | BST descent + expected < 2 rotations |
| **Delete** | **O(log n)** | O(n) | BST descent + rotate down + expected < 2 rotations |
| **Range Query** `[t1, t2]` | **O(log n + k)** | O(n) | Prunes subtrees outside the window |
| **Search** by timestamp | **O(log n)** | O(n) | Standard BST search |
| **Peek most urgent** | **O(1)** | O(1) | Root of the treap |
| **Space** | O(n) | O(n) | One node per event |

The worst case O(n) happens only when the tree degenerates into a chain. Section 4 shows why that is vanishingly unlikely.

**Why the range query is O(log n + k):** the search for the window boundaries follows at most two root-to-leaf paths, costing O(h) = O(log n) expected. Every other visited node lies inside the window and is *reported*, which is the `k` term. Nothing else is touched, because subtrees entirely outside `[t1, t2]` are skipped.

---

## 4. Why the Randomized Heap Invariant Gives Expected O(log n)

### Key idea

All operation costs are proportional to the **depth** of the tree (the height `h`). So it suffices to show the **expected depth of any node is O(log n)**.

For a fixed set of distinct priorities, the heap invariant forces a **unique shape**: the highest-priority node is the root, and the nodes with smaller and larger timestamps form its left and right subtrees, built recursively. This is exactly the shape you get from inserting the keys into a plain BST *in decreasing order of priority*.

If the priority order is a uniformly random permutation relative to the key order, the treap behaves like a **randomly built BST**, which is the same analysis as randomized quicksort.

### Proof that expected depth is O(log n)

Sort all nodes by timestamp and label them `x_1 < x_2 < ... < x_n`. Fix a node `x_i`.

**Step 1 - Ancestor condition.**
Node `x_j` is an ancestor of `x_i` if and only if `x_j` has the **highest priority among all nodes `x_i, ..., x_j`** (the contiguous block of keys between them, inclusive). If some node in that block had higher priority, it would sit above `x_j` and separate `x_i` from `x_j`.

**Step 2 - Probability.**
That block contains `|i - j| + 1` nodes. With a random priority order, each is equally likely to be the maximum, so

```
P(x_j is an ancestor of x_i) = 1 / (|i - j| + 1)
```

**Step 3 - Linearity of expectation.**
Depth of `x_i` = number of its ancestors, so

```
E[depth(x_i)] = sum over j != i of 1 / (|i - j| + 1)

              = (1/2 + 1/3 + ... + 1/i)  +  (1/2 + 1/3 + ... + 1/(n-i+1))

              = (H_i - 1) + (H_(n-i+1) - 1)
```

where `H_m = 1 + 1/2 + ... + 1/m` is the m-th harmonic number.

**Step 4 - Bound.**
Since `H_m <= ln m + 1`:

```
E[depth(x_i)] <= ln i + ln(n - i + 1)  <=  2 ln n  =  O(log n)
```

So every node has expected depth at most about `2 ln n`. Search, insert, delete and the two boundary descents of a range query all cost O(depth) = **O(log n) expected**.

### Why rotations are cheap (expected O(1))

* **Insert:** the new node is placed as a leaf and rotated up while it beats its parent. Each rotation moves it up one level.
* **Delete:** the node is rotated down until it becomes a leaf. The number of rotations equals the length of the right spine of its left subtree plus the left spine of its right subtree.

Both quantities are sums of indicator variables with probabilities of the form `1/(m(m+1))`-style terms that telescope, and the expected total is **less than 2**. So the expensive-looking "rebalancing" step is expected O(1) work, and the cost is dominated by the O(log n) descent.

### Why the worst case is unlikely

A degenerate chain requires a very specific priority ordering. With random tiebreakers, the probability that the height exceeds `c log n` shrinks rapidly (it is `O(1/n^k)` for suitable `c`), so the tree is **O(log n) height with high probability**, not just on average.

### Important condition: what "randomized" means for this project

Our heap priority is the emergency level, which is *not* random by itself. The expected-O(log n) argument needs the **priority order to look random relative to timestamp order**. We ensure this by:

1. Using the composite priority `(emergency, rand)`, where `rand` is a fresh random number drawn at insertion. It randomizes the order among events of the **same** emergency level.
2. Relying on the fact that emergency levels of incoming events are not systematically correlated with arrival time.

> **Known limitation:** if emergency levels were *perfectly correlated* with time (e.g. every new event is strictly more urgent than the last), the tree would degenerate toward a chain and operations would approach O(n). This is the cost of letting a real-world attribute act as the heap priority, and it is why we say **expected** rather than guaranteed O(log n). A fully random priority plus a separate `emergency` field would remove this limitation, at the price of losing the "root = most urgent" property.

---

## 5. Algorithms (Pseudocode)

### Rotations

```
rotateRight(y):            rotateLeft(x):
    x = y.left                 y = x.right
    y.left = x.right           x.right = y.left
    x.right = y                y.left = x
    return x                   return y
```

### Insert

```
insert(node, t, e):
    if node is null:
        return new Node(t, e, rand())
    if t < node.timestamp:
        node.left = insert(node.left, t, e)
        if node.left.priority > node.priority:
            node = rotateRight(node)
    else:
        node.right = insert(node.right, t, e)
        if node.right.priority > node.priority:
            node = rotateLeft(node)
    return node
```

### Delete

```
delete(node, t):
    if node is null: return null
    if t < node.timestamp:
        node.left = delete(node.left, t)
    else if t > node.timestamp:
        node.right = delete(node.right, t)
    else:
        if node.left is null:  return node.right
        if node.right is null: return node.left
        // rotate the higher-priority child up, then keep deleting
        if node.left.priority > node.right.priority:
            node = rotateRight(node)
            node.right = delete(node.right, t)
        else:
            node = rotateLeft(node)
            node.left = delete(node.left, t)
    return node
```

### Range Query `[lo, hi]`

```
rangeQuery(node, lo, hi, result):
    if node is null: return
    if lo < node.timestamp:
        rangeQuery(node.left, lo, hi, result)      // left may hold matches
    if lo <= node.timestamp and node.timestamp <= hi:
        result.add(node)                            // in window: report
    if node.timestamp < hi:
        rangeQuery(node.right, lo, hi, result)     // right may hold matches
```

Results come out in chronological order because the traversal is in-order.

---



## 6. Team

| Member | Role |
|---|---|
| Member 1 | `<Muhammed Nihadh Y>` |
| Member 2 | `<Gautham Madhu >` |
| Member 3 | `<Muhil Prithivi M>` |
| Member 4 | `<Sakthi Sudhan C>`|
