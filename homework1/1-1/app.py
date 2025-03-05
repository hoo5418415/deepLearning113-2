from flask import Flask, render_template, request
import random

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get grid dimension and validate it
        try:
            n = int(request.form.get("grid_size", 3))
            if n < 3 or n > 9:
                n = 3
        except ValueError:
            n = 3

        # Set default starting cell
        start = (0, 0)
        
        # Create list of all positions except the starting cell
        positions = [(i, j) for i in range(n) for j in range(n) if (i, j) != start]
        
        # Randomly choose a goal cell
        goal = random.choice(positions)
        positions.remove(goal)
        
        # Randomly choose a dead cell
        dead = random.choice(positions)
        positions.remove(dead)
        
        # Randomly choose n-2 obstacles from the remaining positions
        obstacles = random.sample(positions, n - 2) if len(positions) >= n - 2 else []
        
        grid = {
            "n": n,
            "start": start,
            "goal": goal,
            "dead": dead,
            "obstacles": obstacles
        }
        
        # Define rewards (these values could be used in your reinforcement learning setup)
        rewards = {
            "goal": 20,
            "dead": -20,
            "obstacle": -1
        }
        
        return render_template("index.html", grid=grid, rewards=rewards)
    else:
        # For GET requests, just show the form
        return render_template("index.html", grid=None)

if __name__ == "__main__":
    app.run(debug=True)