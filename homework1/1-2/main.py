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

        # Randomly select n-2 obstacles from remaining positions
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
#    and Generate a Random Policy that Reaches the Goal,
#    Then Display Results on the Webpage
############################################################

@app.route("/solve", methods=["POST"])
def solve():
    grid_data = session.get("grid_data", None)
    if not grid_data:
        return redirect(url_for("index"))
    
    n = grid_data["n"]
    start = tuple(grid_data["start"])
    goal = tuple(grid_data["goal"])
    dead = tuple(grid_data["dead"])
    obstacles = set(tuple(o) for o in grid_data["obstacles"])

    # Compute the value function using iterative policy evaluation.
    V = iterative_policy_evaluation(n, start, goal, dead, obstacles)
    # Generate a random policy that, when simulated from the start, eventually reaches the goal.
    policy = generate_random_policy_that_reaches_goal(n, start, goal, dead, obstacles, grid_data)
    
    # Render the same grid page, but now include the computed results.
    return render_template("index.html", grid=grid_data, value_matrix=V, policy_matrix=policy)


def iterative_policy_evaluation(n, start, goal, dead, obstacles, gamma=0.9, theta=1e-4, step_cost=-0.1):
    """
    Evaluate the value function under a fixed uniform random policy,
    while not updating the value for obstacle cells (their value remains 0).
    Terminal states (goal, dead) have fixed values.
    """
    V = [[0.0 for _ in range(n)] for _ in range(n)]
    actions = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}
    policy_prob = 1.0 / len(actions)

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

    while True:
        delta = 0
        newV = [[0.0 for _ in range(n)] for _ in range(n)]
        for r in range(n):
            for c in range(n):
                s = (r, c)
                if s in obstacles:
                    newV[r][c] = 0
                    continue
                if is_terminal(s):
                    newV[r][c] = 20.0 if s == goal else -20.0
                    continue
                v_sum = 0.0
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


def random_policy(n, start, goal, dead, obstacles):
    """
    Generate a policy matrix by randomly choosing an action for each non-terminal,
    non-obstacle cell. Terminal cells and obstacles get fixed symbols:
      - Goal cell: "G"
      - Dead cell: "X"
      - Obstacle: "#"
    For other cells, randomly choose among "U", "D", "L", "R" and convert to arrow symbols.
    """
    actions = ["U", "D", "L", "R"]
    policy = [["" for _ in range(n)] for _ in range(n)]
    for r in range(n):
        for c in range(n):
            s = (r, c)
            if s in obstacles:
                policy[r][c] = "#"
            elif s == goal:
                policy[r][c] = "G"
            elif s == dead:
                policy[r][c] = "X"
            else:
                chosen = random.choice(actions)
                if chosen == "U":
                    policy[r][c] = "↑"
                elif chosen == "D":
                    policy[r][c] = "↓"
                elif chosen == "L":
                    policy[r][c] = "←"
                elif chosen == "R":
                    policy[r][c] = "→"
    return policy


def simulate_policy(policy, grid_data, max_steps=100):
    """
    Simulate following the policy from the start cell.
    Returns True if the simulation reaches the goal, otherwise False.
    """
    n = grid_data["n"]
    start = tuple(grid_data["start"])
    goal = tuple(grid_data["goal"])
    dead = tuple(grid_data["dead"])
    obstacles = set(tuple(o) for o in grid_data["obstacles"])
    cell = start
    steps = 0
    while steps < max_steps:
        if cell == goal:
            return True
        r, c = cell
        action = policy[r][c]
        if action not in ["↑", "↓", "←", "→"]:
            return False
        if action == "↑":
            next_cell = (r - 1, c)
        elif action == "↓":
            next_cell = (r + 1, c)
        elif action == "←":
            next_cell = (r, c - 1)
        elif action == "→":
            next_cell = (r, c + 1)
        else:
            next_cell = cell
        if not (0 <= next_cell[0] < n and 0 <= next_cell[1] < n):
            return False
        if next_cell in obstacles or next_cell == dead:
            return False
        cell = next_cell
        steps += 1
    return False


def generate_random_policy_that_reaches_goal(n, start, goal, dead, obstacles, grid_data, max_attempts=1000):
    """
    Generate a random policy repeatedly until the simulation starting at 'start'
    eventually reaches the goal or until max_attempts are reached.
    """
    for _ in range(max_attempts):
        policy = random_policy(n, start, goal, dead, obstacles)
        if simulate_policy(policy, grid_data):
            return policy
    # If none found, return the last generated policy.
    return policy


def generate_random_policy_that_reaches_goal_wrapper(n, start, goal, dead, obstacles, grid_data):
    """
    Wrapper function that returns a random policy which, when followed from start, reaches the goal.
    """
    return generate_random_policy_that_reaches_goal(n, start, goal, dead, obstacles, grid_data)


# In the /solve route, we call this function.
def generate_random_policy_that_reaches_goal(n, start, goal, dead, obstacles, grid_data, max_attempts=1000):
    for _ in range(max_attempts):
        policy = random_policy(n, start, goal, dead, obstacles)
        if simulate_policy(policy, grid_data):
            return policy
    return policy


if __name__ == "__main__":
    app.run(debug=True)