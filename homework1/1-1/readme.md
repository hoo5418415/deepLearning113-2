## Note 只能在本地端執行

prompt


Write a Flask web application to create a reinforcement learning gridworld. The application should fulfill the following requirements:

1. Allow the user to input a dimension n (between 3 and 9) to generate an n×n grid.
    
    nn
    
    n×nn \times n
    
2. Make the starting cell green and allow the user to click on a cell to assign it as the starting position.
3. Designate the goal cell as red and the dead cell as blue.
4. Randomly place n−2 obstacles throughout the grid, which should be visually represented in a different color (e.g., gray).
    
    n−2n-2
    
5. Assign rewards as follows:
    - The goal cell (red) should provide a reward of +20.
    - The dead cell (blue) should incur a penalty of -20.
    - Obstacles should incur a penalty of -1 if hit.
6. Ensure that the grid updates dynamically based on user interactions (e.g., selecting the starting cell and generating the grid).

The application should have a simple and user-friendly interface, displaying the grid with appropriate colors and allowing for user interactions. Include any necessary Flask routes, HTML templates, and JavaScript for handling mouse clicks and grid updates.