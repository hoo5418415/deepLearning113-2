from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import random
import math

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用於 session 加密

# ---------------------------
# 初始化隨機 grid
# ---------------------------
def init_grid(n):
    """
    建立一個 n x n 的網格，隨機分配：
      - 1 個 start（起始點，綠色）
      - 1 個 goal（目標格子，紅色，reward +20，終止）
      - 1 個 dead（死格子，藍色，reward -20，終止）
      - 2 個 obstacle（障礙物，灰色）
    其餘皆為 empty
    """
    all_positions = [(r, c) for r in range(n) for c in range(n)]
    
    start_pos = random.choice(all_positions)
    all_positions.remove(start_pos)
    
    goal_pos = random.choice(all_positions)
    all_positions.remove(goal_pos)
    
    dead_pos = random.choice(all_positions)
    all_positions.remove(dead_pos)
    
    # 固定選 2 個障礙物
    obstacle_count = 2 if len(all_positions) >= 2 else 0
    obstacle_positions = random.sample(all_positions, k=obstacle_count)
    
    # 建立初始 grid（預設 "empty"）
    grid = [['empty' for _ in range(n)] for _ in range(n)]
    
    sr, sc = start_pos
    grid[sr][sc] = 'start'
    
    gr, gc = goal_pos
    grid[gr][gc] = 'goal'
    
    dr, dc = dead_pos
    grid[dr][dc] = 'dead'
    
    for (r, c) in obstacle_positions:
        grid[r][c] = 'obstacle'
    
    return grid

# ---------------------------
# 價值迭代算法
# ---------------------------
def value_iteration(grid):
    """
    對於非障礙且非終止狀態（goal, dead）的格子，執行價值迭代。
    終止狀態：
      - goal: reward +20，value 固定為 20
      - dead: reward -20，value 固定為 -20
    障礙物：視同牆壁，無法進入，value 固定為 0
    其他移動：
      - 每走一步消耗 -1（reward -1）
      - 若移動到 goal 或 dead，則分別獲得 +20 / -20
      - 四方向 deterministic 移動，若出界或撞障礙則停留原地，reward -1
    """
    n = len(grid)
    gamma = 0.9
    threshold = 1e-3
    max_iterations = 100
    
    # 初始化 values：對於 goal 與 dead 直接賦予對應 reward，障礙物為 0，其餘初始 0
    values = [[0.0 for _ in range(n)] for _ in range(n)]
    for r in range(n):
        for c in range(n):
            if grid[r][c] == 'goal':
                values[r][c] = 20.0
            elif grid[r][c] == 'dead':
                values[r][c] = -20.0
            elif grid[r][c] == 'obstacle':
                values[r][c] = 0.0

    # 定義四個方向移動
    directions = {
        '↑': (-1, 0),
        '↓': (1, 0),
        '←': (0, -1),
        '→': (0, 1),
    }
    
    # 給定狀態 (r, c) 回傳各個 action 的 (next_state, reward)
    def get_actions_and_next_states(r, c):
        # 若當前狀態為終止狀態 (goal 或 dead)，動作皆返回自己，reward 0
        if grid[r][c] in ['goal', 'dead']:
            return { a: ((r, c), 0.0) for a in directions }
        
        results = {}
        for a, (dr, dc) in directions.items():
            nr, nc = r + dr, c + dc
            # 出界或撞到障礙：停留原地，reward -1
            if nr < 0 or nr >= n or nc < 0 or nc >= n:
                results[a] = ((r, c), -1.0)
            elif grid[nr][nc] == 'obstacle':
                results[a] = ((r, c), -1.0)
            elif grid[nr][nc] == 'goal':
                results[a] = ((nr, nc), 20.0)
            elif grid[nr][nc] == 'dead':
                results[a] = ((nr, nc), -20.0)
            else:
                results[a] = ((nr, nc), -1.0)
        return results

    # 迭代計算
    for _ in range(max_iterations):
        delta = 0.0
        new_values = [[values[r][c] for c in range(n)] for r in range(n)]
        for r in range(n):
            for c in range(n):
                # 對於障礙或終止狀態（goal, dead），value 固定
                if grid[r][c] in ['obstacle', 'goal', 'dead']:
                    continue
                actions_info = get_actions_and_next_states(r, c)
                candidate_vals = []
                for a, (next_state, rew) in actions_info.items():
                    nr, nc = next_state
                    candidate_vals.append(rew + gamma * values[nr][nc])
                best_val = max(candidate_vals) if candidate_vals else 0.0
                new_values[r][c] = best_val
                delta = max(delta, abs(best_val - values[r][c]))
        values = new_values
        if delta < threshold:
            break

    # 根據收斂後的 values 推導最優策略
    policy = [['' for _ in range(n)] for _ in range(n)]
    for r in range(n):
        for c in range(n):
            cell = grid[r][c]
            if cell == 'obstacle':
                policy[r][c] = 'X'  # 障礙
            elif cell == 'goal':
                policy[r][c] = 'G'  # 目標
            elif cell == 'dead':
                policy[r][c] = 'D'  # 死格子
            elif cell == 'start':
                # 顯示起始點標記
                policy[r][c] = 'S'
            else:
                # 對於 empty（或其他非終止格），選取最佳動作
                actions_info = get_actions_and_next_states(r, c)
                best_a = None
                best_val = -math.inf
                for a, (next_state, rew) in actions_info.items():
                    nr, nc = next_state
                    val = rew + gamma * values[nr][nc]
                    if val > best_val:
                        best_val = val
                        best_a = a
                policy[r][c] = best_a if best_a is not None else ''
    return policy, values

# ---------------------------
# Flask 路由與 API
# ---------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """
    使用者輸入 n (3~7)，後端隨機生成 grid：
      - 1 個 start
      - 1 個 goal (red, reward +20)
      - 1 個 dead (blue, penalty -20)
      - 2 個 obstacle (gray)
    """
    data = request.json
    n = int(data['n'])
    if n < 3 or n > 7:
        return jsonify({'error': 'n 必須在 3~7 之間'}), 400
    
    grid = init_grid(n)
    session['n'] = n
    session['grid'] = grid
    return jsonify({'grid': grid})

@app.route('/update_cell', methods=['POST'])
def update_cell():
    """
    使用者點擊格子 (row, col, mode)：
      mode 可為：
        - 'start'：設定起始點（先清除原先 start）
        - 'goal'：設定目標（清除原有 goal）
        - 'dead'：設定死格子（若點擊的格子已是 dead，則回復為 empty）
        - 'obstacle'：放置障礙物（若點擊的格子已是 obstacle，則回復為 empty）
    """
    if 'grid' not in session:
        return jsonify({'error': '尚未生成 grid'}), 400

    data = request.json
    row = data['row']
    col = data['col']
    mode = data['mode']

    grid = session['grid']
    n = len(grid)
    if not (0 <= row < n and 0 <= col < n):
        return jsonify({'error': '超出格子範圍'}), 400

    if mode == 'start':
        # 清除所有舊的起始點
        for r in range(n):
            for c in range(n):
                if grid[r][c] == 'start':
                    grid[r][c] = 'empty'
        grid[row][col] = 'start'

    elif mode == 'goal':
        # 清除所有舊的目標格子
        for r in range(n):
            for c in range(n):
                if grid[r][c] == 'goal':
                    grid[r][c] = 'empty'
        grid[row][col] = 'goal'

    elif mode == 'dead':
        # 若該格已是 dead，則回復為 empty（路徑）；否則先清除現有的 dead，再設為 dead
        if grid[row][col] == 'dead':
            grid[row][col] = 'empty'
        else:
            for r in range(n):
                for c in range(n):
                    if grid[r][c] == 'dead':
                        grid[r][c] = 'empty'
            grid[row][col] = 'dead'

    elif mode == 'obstacle':
        # 若該格已是 obstacle，則回復為 empty（路徑）；否則若格子非 start/goal/dead，則設為 obstacle
        if grid[row][col] == 'obstacle':
            grid[row][col] = 'empty'
        else:
            if grid[row][col] in ['start', 'goal', 'dead']:
                return jsonify({'error': '無法在此格放置障礙物'}), 400
            grid[row][col] = 'obstacle'
    else:
        return jsonify({'error': '未知的 mode'}), 400

    session['grid'] = grid
    return jsonify({'grid': grid})

@app.route('/value_iteration', methods=['POST'])
def run_value_iteration():
    if 'grid' not in session:
        return jsonify({'error': '尚未生成 grid'}), 400
    grid = session['grid']
    policy, values = value_iteration(grid)
    # 轉換 value 為 round 過的小數
    values_str = [[round(val, 2) for val in row] for row in values]
    return jsonify({
        'policy': policy,
        'values': values_str
    })

if __name__ == '__main__':
    app.run(debug=True)