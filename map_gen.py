import random

def generate_path(cols, rows):
    path = []
    grid = [[0]*cols for _ in range(rows)]
    
    c, r = cols//2, 0
    path.append((c, r))
    grid[r][c] = 1
    
    while r < rows - 1:
        moves = []
        if c > 0 and grid[r][c-1] == 0: moves.append((-1, 0))
        if c < cols-1 and grid[r][c+1] == 0: moves.append((1, 0))
        if r < rows-1 and grid[r+1][c] == 0: moves.append((0, 1))
        
        if not moves:
            if r < rows-1:
                r += 1
                path.append((c, r))
                grid[r][c] = 1
            else:
                break
        else:
            dc, dr = random.choice(moves)
            c += dc
            r += dr
            path.append((c, r))
            grid[r][c] = 1
            
    return path, grid
