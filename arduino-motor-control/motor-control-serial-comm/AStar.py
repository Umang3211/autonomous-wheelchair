from typing import List, Tuple, Dict, Set
import numpy as np
import heapq
from math import sqrt
import matplotlib.pyplot as plt

def create_node(position: Tuple[int, int], g: float = float("inf"), h: float = 0.0, parent: Dict = None) -> Dict:
    return {
        "position": position, # x, y of current node
        "g": g, # cost from starting node to current node
        "h": h, # cost from current node to goal node
        "f": g+h,
        "parent": parent # parent node, setting to default none
    }

def calculate_heuristic(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    x1, y1 = pos1
    x2, y2 = pos2

    # calculate the euclidean distance between these two
    return sqrt((x2-x1)**2 + (y2-y1)**2)

def get_valid_neighbors(grid: np.ndarray, position: Tuple[int, int]) -> List[Tuple[int, int]]:
    # find valid neighbors
    x, y = position
    rows, cols = grid.shape

    possible_moves = [
        (x+1, y), (x-1, y),
        (x, y+1), (x, y-1),
        (x+1, y+1), (x-1, y-1),
        (x+1, y-1), (x-1, y+1)
    ]

    return [
        (nx, ny) for nx, ny in possible_moves
        if 0 <= nx < rows and 0 <= ny < cols # does not go outside of current grid
        and grid[nx, ny] == 0 # no obstalces
    ]

def reconstruct_path(goal_node: Dict) -> List[Tuple[int, int]]:
    path = []
    current = goal_node

    while current is not None:
        path.append(current["position"])
        current = current["parent"]

    # reverse path (start -> goal instead of goal -> start)
    return path[::-1]

def find_path(grid: np.ndarray, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
    start_node = create_node(
        position=start,
        g=0,
        h=calculate_heuristic(start, goal)
    )

    open_list = [(start_node["f"], start)] # priority queue for having the most efficient node at the top
    open_dict = {start: start_node} # node look ups (hash map)
    closed_set = set() # all nodes that we hv currently explored

    while open_list:
        _, current_pos = heapq.heappop(open_list)
        current_node = open_dict[current_pos]

        if current_pos == goal:
            return reconstruct_path(current_node)
        
        closed_set.add(current_pos)

        for neighbor_pos in get_valid_neighbors(grid, current_pos):
            if neighbor_pos in closed_set:
                continue

            tentative_g = current_node["g"] + calculate_heuristic(current_pos, neighbor_pos)

            if neighbor_pos not in open_dict:
                neighbor = create_node(
                    position=neighbor_pos,
                    g=tentative_g,
                    h=calculate_heuristic(neighbor_pos, goal),
                    parent=current_node
                )

                heapq.heappush(open_list, (neighbor["f"], neighbor_pos))
                open_dict[neighbor_pos] = neighbor
            
            elif tentative_g < open_dict[neighbor_pos]["g"]:
                neighbor = open_dict[neighbor_pos]
                neighbor["g"] = tentative_g
                neighbor["f"] = tentative_g + neighbor["h"]
                neighbor["parent"] = current_node
    return []

def viz_path(grid: np.ndarray, path: List[Tuple[int, int]]):
    plt.figure(figsize=(10,10))
    plt.imshow(grid, cmap="binary")

    if path:
        path = np.array(path)
        plt.plot(path[:, 1], path[:, 0], "b-", linewidth=3, label="Path")
        plt.plot(path[0, 1], path[0, 0], "go", markersize=15, label="Start")
        plt.plot(path[-1, 1], path[-1, 0], "ro", markersize=15, label="Goal")

    plt.grid(True)
    plt.legend(fontsize=12)
    plt.title("A* Pathfinding Result")
    plt.show()

grid = np.zeros((20, 20))
grid[5:15, 10] = 1
grid[5, 5:15] = 1
start_pos = (2, 2)
end_pos = (19, 10)
path = find_path(grid, start_pos, end_pos)
if path:
    print(f"Path found with {len(path)} steps")
    viz_path(grid, path)
else:
    print("No path found")