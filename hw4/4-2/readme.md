# DQN, Double DQN, Dueling DQN Comparison in GridWorld

This project implements and compares three reinforcement learning algorithms — **DQN**, **Double DQN**, and **Dueling DQN** — in a custom GridWorld environment. The workflow is organized according to the CRISP-DM (Cross-Industry Standard Process for Data Mining) methodology, ensuring best practices for applied machine learning projects.

---

## CRISP-DM Workflow

### 1. Business Understanding

- **Goal:**  
  To investigate and compare the learning performance of DQN, Double DQN, and Dueling DQN in a deterministic 4x4 GridWorld environment.
- **Key Questions:**  
  - Which algorithm converges faster and more stably?
  - Can Double DQN reduce Q-value overestimation?
  - Does Dueling DQN provide more robust value estimation for different states?

---

### 2. Data Understanding

- **Source:**  
  Data comes from interactions between the agent and the GridWorld environment (see `GridBoard.py` and `Gridworld.py`).
- **Environment Details:**  
  - **State:** Encoded as a 4x4x4 NumPy array (flattened to a 64-dimensional vector).
  - **Actions:** Up (`u`), Down (`d`), Left (`l`), Right (`r`), encoded as integers [0, 1, 2, 3].
  - **Rewards:**  
    - `+10` for reaching the goal  
    - `-10` for falling into a pit  
    - `-1` for each non-terminal move

---

### 3. Data Preparation

- **Process:**  
  Agents interact with the environment in an online fashion (no offline dataset).  
  Each experience tuple consists of:  
  `(state, action, reward, next_state, done)`
- **Buffer:**  
  A replay buffer is used for experience replay, enabling more stable and efficient learning.
- **State Processing:**  
  The state is obtained from `env.board.render_np().flatten()` to serve as input to the neural network.

---

### 4. Modeling

- **Algorithms:**
  - **DQN:**  
    Standard Deep Q-Network with target network for stability.
  - **Double DQN:**  
    Separates action selection and value evaluation using two networks, reducing Q-value overestimation.
  - **Dueling DQN:**  
    Neural architecture splits into "Value" and "Advantage" streams, improving value estimation for different states.
- **Neural Network:**  
  - **Input:** 64-dimensional state vector
  - **Output:** 4 Q-values (for each action)
  - **Loss:** Mean Squared Error (MSE) between predicted Q and target Q
- **Training Loop:**  
  - Initialize environment and agent
  - For each episode:
    - Observe state
    - Choose action via ε-greedy policy
    - Interact with environment
    - Store experience in replay buffer
    - Sample batch, compute target, update network
    - Update target network periodically

---

### 5. Evaluation

- **Metrics:**  
  - Episode total reward (per episode, to measure learning progress)
  - Convergence speed
  - Training stability (variance)
- **Visualization:**  
  - Learning curves are plotted for all three algorithms for easy comparison.
  
---

### 6.Deployment

- **How to Use:**
	Clone the repository and place GridBoard.py and Gridworld.py in the root directory.
	Run main.py to train and compare the three algorithms.
	Review the output learning curves for analysis.

### Extensibility:

Change hyperparameters, environment size, or reward structure to further explore the effects on learning.

The codebase can be easily extended to other RL algorithms or environments.
