import numpy as np
import matplotlib.pyplot as plt

# 全域設定中文顯示
plt.rc('font', family='Microsoft JhengHei')

# 模擬參數
num_arms   = 10      # 臂數
num_steps  = 1000    # 每次實驗步數
num_runs   = 100     # 重複實驗次數
epsilon    = 0.1     # Epsilon-Greedy 探索率
ucb_c      = 2       # UCB 中調控探索的參數
tau        = 0.1     # Softmax 的溫度參數

# 每次實驗中，各臂的真實成功率 (Bernoulli 問題), 每次實驗隨機產生
# ※注意：四個算法均以相同的 true_probs 進行模擬比較
def generate_true_probs():
    return np.random.rand(num_arms)

# Epsilon-Greedy 模擬 (使用 Bernoulli 獎勵)
def simulate_epsilon_greedy(epsilon, true_probs, num_steps):
    Q = np.zeros(num_arms)       # 各臂估計獎勵
    N = np.zeros(num_arms)       # 各臂選取次數
    rewards = np.zeros(num_steps)
    
    for t in range(num_steps):
        if np.random.rand() < epsilon:
            arm = np.random.randint(num_arms)
        else:
            arm = np.argmax(Q)
        # Bernoulli 獎勵
        reward = 1 if np.random.rand() < true_probs[arm] else 0
        N[arm] += 1
        Q[arm] += (reward - Q[arm]) / N[arm]
        rewards[t] = reward
    return rewards

# UCB 模擬 (使用 Bernoulli 獎勵)
def simulate_ucb(ucb_c, true_probs, num_steps):
    Q = np.zeros(num_arms)
    # 為避免除 0，初始每個臂視為被拉取過 1 次
    N = np.ones(num_arms)
    rewards = np.zeros(num_steps)
    
    # 前 num_arms 步：各臂各拉一次
    for arm in range(num_arms):
        reward = 1 if np.random.rand() < true_probs[arm] else 0
        Q[arm] = reward
        rewards[arm] = reward
    
    for t in range(num_arms, num_steps):
        ucb_values = Q + ucb_c * np.sqrt(np.log(t + 1) / N)
        arm = np.argmax(ucb_values)
        reward = 1 if np.random.rand() < true_probs[arm] else 0
        N[arm] += 1
        Q[arm] += (reward - Q[arm]) / N[arm]
        rewards[t] = reward
    return rewards

# Softmax 模擬 (使用 Bernoulli 獎勵)
def simulate_softmax(tau, true_probs, num_steps):
    Q = np.zeros(num_arms)
    N = np.zeros(num_arms)
    rewards = np.zeros(num_steps)
    
    for t in range(num_steps):
        exp_values = np.exp(Q / tau)
        probs = exp_values / np.sum(exp_values)
        arm = np.random.choice(np.arange(num_arms), p=probs)
        reward = 1 if np.random.rand() < true_probs[arm] else 0
        N[arm] += 1
        Q[arm] += (reward - Q[arm]) / N[arm]
        rewards[t] = reward
    return rewards

# Thompson Sampling 模擬 (Bernoulli 問題, 使用 Beta 分布)
def simulate_thompson(true_probs, num_steps):
    S = np.zeros(num_arms)    # 成功次數
    F = np.zeros(num_arms)    # 失敗次數
    rewards = np.zeros(num_steps)
    
    for t in range(num_steps):
        # 為每個臂採樣
        theta_samples = np.array([np.random.beta(S[a] + 1, F[a] + 1) for a in range(num_arms)])
        arm = np.argmax(theta_samples)
        reward = 1 if np.random.rand() < true_probs[arm] else 0
        if reward == 1:
            S[arm] += 1
        else:
            F[arm] += 1
        rewards[t] = reward
    return rewards

# 累積獎勵曲線累計 (各算法)
cum_rewards_eps      = np.zeros(num_steps)
cum_rewards_ucb      = np.zeros(num_steps)
cum_rewards_softmax  = np.zeros(num_steps)
cum_rewards_thompson = np.zeros(num_steps)

# 多次實驗取平均
for run in range(num_runs):
    true_probs = generate_true_probs()  # 為本次實驗產生不同的真實成功率
    rewards_eps = simulate_epsilon_greedy(epsilon, true_probs, num_steps)
    rewards_ucb = simulate_ucb(ucb_c, true_probs, num_steps)
    rewards_soft = simulate_softmax(tau, true_probs, num_steps)
    rewards_thom = simulate_thompson(true_probs, num_steps)
    
    cum_rewards_eps      += np.cumsum(rewards_eps)
    cum_rewards_ucb      += np.cumsum(rewards_ucb)
    cum_rewards_softmax  += np.cumsum(rewards_soft)
    cum_rewards_thompson += np.cumsum(rewards_thom)

# 平均累積獎勵
cum_rewards_eps      /= num_runs
cum_rewards_ucb      /= num_runs
cum_rewards_softmax  /= num_runs
cum_rewards_thompson /= num_runs

# 繪圖展示四種算法的累積獎勵比較
plt.figure(figsize=(12,8))
plt.plot(cum_rewards_eps,      label='Epsilon-Greedy')
plt.plot(cum_rewards_ucb,      label='UCB')
plt.plot(cum_rewards_softmax,  label='Softmax')
plt.plot(cum_rewards_thompson, label='Thompson Sampling')
plt.xlabel('步數')
plt.ylabel('累積獎勵')
plt.title('多臂強盜四種算法的累積獎勵比較')
plt.legend()
plt.show()