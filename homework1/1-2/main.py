import random
from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "your_secret_key"  # For session usage

############################################################
# 1. Web Interface: Generate Grid
############################################################

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get grid size from form (allowed: 5-9)
        try:
            n = int(request.form.get("grid_size", 5))
            if n < 5 or n > 9:
                n = 5
        except ValueError:
            n = 5

        # Generate grid configuration:
        # Fixed start at (0, 0)
        start = (0, 0)
        positions = [(i, j) for i in range(n) for j in range(n) if (i, j) != start]

        # Randomly select a goal cell and a dead cell
        goal = random.choice(positions)
        positions.remove(goal)
        dead = random.choice(positions)
        positions.remove(dead)

        # Randomly select n-2 obstacles from the remaining positions
        obstacle_count = n - 2
        obstacles = random.sample(positions, obstacle_count) if len(positions) >= obstacle_count else []

        # Save grid data in session for later use
        session["grid_data"] = {
            "n": n,
            "start": start,
            "goal": goal,
            "dead": dead,
            "obstacles": obstacles
        }
        # Render grid page (results not yet computed)
        return render_template("index.html", grid=session["grid_data"])
    
    # GET: Only display the form (no grid yet)
    return render_template("index.html", grid=None)


############################################################
# 2. Compute Value Function using Iterative Policy Evaluation,
#    Derive Greedy Policy, and Display Results on the Webpage
############################################################

@app.route("/solve", methods=["POST"])
def solve():
    grid_data = session.get("grid_data", None)
    if not grid_data:
        # If grid not generated, redirect to the form
        return redirect(url_for("index"))
    
    n = grid_data["n"]
    start = grid_data["start"]
    goal = grid_data["goal"]
    dead = grid_data["dead"]
    obstacles = set(grid_data["obstacles"])

    # Compute the value function using iterative policy evaluation.
    V = iterative_policy_evaluation(n, start, goal, dead, obstacles)
    # Derive a greedy policy from the computed value function.
    policy = derive_policy_from_value(V, n, start, goal, dead, obstacles)
    
    # Render the same grid page, but now include the results
    return render_template("index.html", grid=grid_data, value_matrix=V, policy_matrix=policy)


def iterative_policy_evaluation(n, start, goal, dead, obstacles, gamma=0.9, theta=1e-4, step_cost=-0.1):
    """
    Evaluate the value function under a fixed uniform random policy,
    while not updating the value for obstacle cells (their value remains 0).

    For non-terminal and non-obstacle states:
      V(s) = sum_{a in A} [1/|A| * ( R(s, a) + gamma * V(s') ) ]
    Terminal states (goal, dead) are fixed.
    """
    # Initialize value function: V(s)=0 for all states.
    V = [[0.0 for _ in range(n)] for _ in range(n)]
    actions = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
    policy_prob = 1.0 / len(actions)  # Uniform random policy

    def is_terminal(s):
        return s == goal or s == dead

    def step(s, action_key):
        # Returns next state and reward for given state and action.
        r, c = s
        if is_terminal(s):
            return s, 0
        dr, dc = actions[action_key]
        nr, nc = r + dr, c + dc
        # Check boundaries
        if nr < 0 or nr >= n or nc < 0 or nc >= n:
            return s, step_cost
        # If moving into an obstacle, agent remains and gets penalty -1
        if (nr, nc) in obstacles:
            return s, -1
        # Check for terminal cells
        if (nr, nc) == goal:
            return (nr, nc), 20
        if (nr, nc) == dead:
            return (nr, nc), -20
        return (nr, nc), step_cost

    # Iterative policy evaluation loop
    while True:
        delta = 0
        newV = [[0.0 for _ in range(n)] for _ in range(n)]
        for r in range(n):
            for c in range(n):
                s = (r, c)
                # Skip obstacles: their value remains 0.
                if s in obstacles:
                    newV[r][c] = 0
                    continue
                # Terminal states have fixed values.
                if is_terminal(s):
                    newV[r][c] = 20.0 if s == goal else -20.0
                    continue

                v_sum = 0.0
                # Sum over all actions (uniform probability).
                for a in actions:
                    next_state, reward = step(s, a)
                    ns_r, ns_c = next_state
                    v_sum += policy_prob * (reward + gamma * V[ns_r][ns_c])
                newV[r][c] = v_sum
                delta = max(delta, abs(newV[r][c] - V[r][c]))
        V = newV
        if delta < theta:
            break

    return V


def derive_policy_from_value(V, n, start, goal, dead, obstacles, gamma=0.9, step_cost=-0.1):
    """
    Given a value function V computed via iterative policy evaluation,
    derive a greedy policy for each non-terminal, non-obstacle state.
    """
    actions = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
    policy = [["" for _ in range(n)] for _ in range(n)]
    
    def is_terminal(s):
        return s == goal or s == dead
    
    def step(s, action_key):
        r, c = s
        if is_terminal(s):
            return s, 0
        dr, dc = actions[action_key]
        nr, nc = r + dr, c + dc
        if nr < 0 or nr >= n or nc < 0 or nc >= n:
            return s, step_cost
        if (nr, nc) in obstacles:
            return s, -1
        if (nr, nc) == goal:
            return (nr, nc), 20
        if (nr, nc) == dead:
            return (nr, nc), -20
        return (nr, nc), step_cost

    for r in range(n):
        for c in range(n):
            s = (r, c)
            # For obstacles, mark policy as "#" and skip evaluation.
            if s in obstacles:
                policy[r][c] = "#"
                continue
            if s == goal:
                policy[r][c] = "G"
            elif s == dead:
                policy[r][c] = "X"
            else:
                best_a = None
                best_val = float("-inf")
                for a in actions:
                    next_state, reward = step(s, a)
                    ns_r, ns_c = next_state
                    value = reward + gamma * V[ns_r][ns_c]
                    if value > best_val:
                        best_val = value
                        best_a = a
                if best_a == "U":
                    policy[r][c] = "↑"
                elif best_a == "D":
                    policy[r][c] = "↓"
                elif best_a == "L":
                    policy[r][c] = "←"
                elif best_a == "R":
                    policy[r][c] = "→"
                else:
                    policy[r][c] = "."
    return policy


if __name__ == "__main__":
    app.run(debug=True)