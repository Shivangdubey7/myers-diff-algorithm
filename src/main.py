import sys


def read_file_as_lines(path: str) -> list[bytes] | None:
    """
    Read a file as raw bytes and split into lines according to assignment rules.
    
    Returns None if file cannot be read, otherwise a list of byte lines.
    Rules:
    - Read as binary (not text) to preserve exact bytes including \r
    - Split on \n byte
    - Drop final empty piece (so trailing \n doesn't create empty line)
    - Keep \r as part of line (\r\n and \n are different lines)
    """
    try:
        # Binary mode preserves exact bytes, doesn't convert line endings
        with open(path, "rb") as f:
            content = f.read()
    except Exception:
        return None
    
    # Split on newline byte \n
    lines = content.split(b"\n")
    
    # If the last piece is empty, drop it (trailing newline creates no extra line)
    if lines and lines[-1] == b"":
        lines.pop()
    
    return lines


def myers_diff(a: list, b: list) -> list[tuple[str, int, int]]:
    """
    Myers' O(ND) diff algorithm - finds the shortest edit script.
    
    Algorithm explanation:
    - Edit graph: imagine an (n+1)×(m+1) grid where horizontal moves = delete from a,
      vertical moves = insert from b, diagonal moves = matching elements (free)
    - Goal: find shortest path from (0,0) to (n,m)
    - D-paths: paths with exactly D edits (non-diagonal moves)
    - For each D, we explore all possible D-paths
    - V[k] stores the furthest x coordinate reached on diagonal k (where k = x - y)
    - A "snake" is a sequence of matching diagonal moves
    
    Returns a list of (operation, a_idx, b_idx) tuples representing the edit script.
    Operations: 'keep' (match), 'delete' (remove from a), 'insert' (add from b)
    
    Time complexity: O(ND) where N = len(a) + len(b), D = edit distance
    Space complexity: O(D²) for history storage
    """
    n, m = len(a), len(b)
    max_d = n + m  # Maximum possible edit distance (all deletes + all inserts)
    
    # V[k] stores the furthest reaching x coordinate on diagonal k
    # Diagonal k means x - y = k (where (x,y) is position in edit graph)
    v = {}
    
    # Store history of V arrays for backtracking to reconstruct the path
    history = []
    
    # Try increasing edit distances from 0 to max_d
    for d in range(max_d + 1):
        # Save current state for backtracking
        history.append(v.copy())
        
        # For D edits, we can reach diagonals from -D to D (in steps of 2)
        # k changes by 2 because each horizontal/vertical move changes k by ±1
        for k in range(-d, d + 1, 2):
            # Decide whether to move down (insert) or right (delete)
            # Move down if: we're at bottom edge, or down path goes further than right
            if k == -d or (k != d and v.get(k - 1, -1) < v.get(k + 1, -1)):
                # Go down (insert from b) - come from diagonal k+1
                x = v.get(k + 1, 0)
            else:
                # Go right (delete from a) - come from diagonal k-1
                x = v.get(k - 1, 0) + 1
            
            # Calculate y from x and k (since k = x - y)
            y = x - k
            
            # Follow the snake (matching elements) - these are free moves
            # Keep going diagonally while elements match
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1
            
            # Store furthest point reached on diagonal k
            v[k] = x
            
            # Check if we've reached the end (bottom-right corner)
            if x == n and y == m:
                # Found shortest path! Backtrack to build the edit script
                return backtrack(history, a, b, d)
    
    # Empty diff (shouldn't reach here if inputs are valid)
    return []


def backtrack(history: list[dict], a: list, b: list, d: int) -> list[tuple[str, int, int]]:
    """
    Backtrack through the edit graph to reconstruct the shortest edit script.
    
    We have the history of V arrays showing furthest points reached at each D.
    Work backwards from the endpoint to build the sequence of operations.
    
    Process:
    1. Start at (n, m) with D edits
    2. For each D, determine which diagonal we came from
    3. Walk back along the snake (matching elements)
    4. Identify the edit operation (insert or delete) that got us to this diagonal
    5. Repeat until we reach (0, 0)
    """
    n, m = len(a), len(b)
    x, y = n, m  # Start at the end
    
    # Build path in reverse (from end to start)
    path = []
    
    # Work backwards through each edit distance level
    for depth in range(d, -1, -1):
        v = history[depth]
        k = x - y  # Current diagonal
        
        # Determine which diagonal we came from to reach diagonal k
        # This reverses the logic from myers_diff
        if k == -depth or (k != depth and v.get(k - 1, -1) < v.get(k + 1, -1)):
            prev_k = k + 1  # We moved down (inserted), so came from k+1
        else:
            prev_k = k - 1  # We moved right (deleted), so came from k-1
        
        # Get the position before the edit operation
        prev_x = v.get(prev_k, 0)
        prev_y = prev_x - prev_k
        
        # Walk back along the snake (all the matching elements)
        # These are 'keep' operations
        while x > prev_x and y > prev_y:
            x -= 1
            y -= 1
            path.append(('keep', x, y))
        
        # Add the edit operation that got us to this diagonal (if not at start)
        if depth > 0:
            if x == prev_x:
                # Vertical move (insertion from b)
                y -= 1
                path.append(('insert', x, y))
            else:
                # Horizontal move (deletion from a)
                x -= 1
                path.append(('delete', x, y))
    
    # Reverse to get forward order (start to end)
    path.reverse()
    return path


def print_line_diff(a_lines: list[bytes], b_lines: list[bytes]):
    """
    Print the line diff in Part A format (lines command).
    
    Output format:
    - Space prefix: line exists in both files (keep)
    - Minus prefix: line only in file A (delete)
    - Plus prefix: line only in file B (insert)
    
    The delete-first rule is automatically satisfied because our edit script
    maintains the order from the backtracking process.
    """
    script = myers_diff(a_lines, b_lines)
    
    for op, a_idx, b_idx in script:
        if op == 'keep':
            # Line exists in both files - print with space prefix
            sys.stdout.buffer.write(b" ")
            sys.stdout.buffer.write(a_lines[a_idx])
            sys.stdout.buffer.write(b"\n")
        elif op == 'delete':
            # Line only in A - print with minus prefix
            sys.stdout.buffer.write(b"-")
            sys.stdout.buffer.write(a_lines[a_idx])
            sys.stdout.buffer.write(b"\n")
        elif op == 'insert':
            # Line only in B - print with plus prefix
            sys.stdout.buffer.write(b"+")
            sys.stdout.buffer.write(b_lines[b_idx])
            sys.stdout.buffer.write(b"\n")


def char_diff_ranges(old_line: bytes, new_line: bytes) -> tuple[str, str]:
    """
    Compute character-level diff ranges for a line pair (Part B).
    
    Process:
    1. Decode both lines as UTF-8 to Unicode code points
    2. Run Myers' diff on the character sequences
    3. Collect positions of changed characters
    4. Convert positions to range format (start-end, merged touching ranges)
    
    Returns (old_ranges, new_ranges) as strings, e.g., ("3-5,9-12", "3-7")
    Uses "." if no changes on that side.
    
    Range format:
    - 0-indexed character positions (Unicode code points, not bytes)
    - end position not included (11-12 means single char at pos 11)
    - Multiple ranges comma-separated with no spaces
    - Touching ranges merged (3-7 not 3-5,5-7)
    """
    # Decode to Unicode code points (emojis count as 1 character)
    try:
        old_str = old_line.decode('utf-8')
        new_str = new_line.decode('utf-8')
    except UnicodeDecodeError:
        # If decoding fails, return no changes
        return ".", "."
    
    # Convert to list of code points (characters)
    # In Python, string iteration gives us code points automatically
    old_chars = list(old_str)
    new_chars = list(new_str)
    
    # Run Myers' diff on characters (reusing our algorithm!)
    script = myers_diff(old_chars, new_chars)
    
    # Collect changed character positions
    old_positions = []
    new_positions = []
    
    for op, old_idx, new_idx in script:
        if op == 'delete':
            old_positions.append(old_idx)
        elif op == 'insert':
            new_positions.append(new_idx)
    
    # Convert positions to range strings
    def positions_to_ranges(positions: list[int]) -> str:
        """Convert list of positions to range string like '3-5,9-12'."""
        if not positions:
            return "."
        
        positions.sort()
        ranges = []
        start = positions[0]
        end = positions[0] + 1  # end is exclusive
        
        # Merge consecutive positions into ranges
        for pos in positions[1:]:
            if pos == end:
                # Extend current range
                end = pos + 1
            else:
                # Save current range and start new one
                ranges.append(f"{start}-{end}")
                start = pos
                end = pos + 1
        
        # Add final range
        ranges.append(f"{start}-{end}")
        return ",".join(ranges)
    
    old_ranges = positions_to_ranges(old_positions)
    new_ranges = positions_to_ranges(new_positions)
    
    return old_ranges, new_ranges


def print_highlight_diff(a_lines: list[bytes], b_lines: list[bytes]):
    """
    Print the diff with character-level highlighting (Part B - highlight command).
    
    Process:
    1. Run line-level diff to get edit script
    2. Group consecutive deletes and inserts into change blocks
    3. For each change block, apply delete-first rule:
       - Print all delete lines
       - Print all insert lines
       - After each insert line that has a paired delete, print character ranges
    
    Pairing rule: 1st delete pairs with 1st insert, 2nd with 2nd, etc.
    Unpaired lines get no character diff line.
    
    Output format for character ranges:
    ? <old_ranges> | <new_ranges>
    Example: ? 12-13 | 11-12
    """
    script = myers_diff(a_lines, b_lines)
    
    # Track current change block (consecutive deletes and inserts)
    change_block_deletes = []
    change_block_inserts = []
    
    def flush_change_block():
        """
        Output a complete change block with delete-first rule and character pairing.
        
        The delete-first rule requires all deletes to appear before any inserts
        within a change block (group of consecutive edits with no keep between).
        """
        # Print all deletes first
        for line in change_block_deletes:
            sys.stdout.buffer.write(b"-")
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.write(b"\n")
        
        # Print all inserts with character diff annotations
        for i, line in enumerate(change_block_inserts):
            sys.stdout.buffer.write(b"+")
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.write(b"\n")
            
            # Pair with corresponding delete if it exists (same index)
            if i < len(change_block_deletes):
                old_ranges, new_ranges = char_diff_ranges(
                    change_block_deletes[i], 
                    change_block_inserts[i]
                )
                # Print character diff line
                range_line = f"? {old_ranges} | {new_ranges}\n"
                sys.stdout.buffer.write(range_line.encode('utf-8'))
        
        # Clear for next change block
        change_block_deletes.clear()
        change_block_inserts.clear()
    
    # Process the edit script
    for op, a_idx, b_idx in script:
        if op == 'keep':
            # Keep operation ends current change block (if any)
            if change_block_deletes or change_block_inserts:
                flush_change_block()
            
            # Print keep line with space prefix
            sys.stdout.buffer.write(b" ")
            sys.stdout.buffer.write(a_lines[a_idx])
            sys.stdout.buffer.write(b"\n")
        elif op == 'delete':
            # Add to current change block
            change_block_deletes.append(a_lines[a_idx])
        elif op == 'insert':
            # Add to current change block
            change_block_inserts.append(b_lines[b_idx])
    
    # Flush final change block if script ends with edits
    if change_block_deletes or change_block_inserts:
        flush_change_block()


def main() -> int:
    """
    Main entry point for the Myers' diff program.
    
    Usage: main.py lines|highlight A_PATH B_PATH
    
    Commands:
    - lines: Print line-level diff (Part A)
    - highlight: Print line-level diff with character-level changes (Part B)
    
    Exit codes:
    - 0: Success
    - 2: Invalid arguments or file read error
    """
    # Validate command-line arguments
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A_PATH B_PATH", file=sys.stderr)
        return 2
    
    command, a_path, b_path = sys.argv[1:]
    
    # Read both files as raw bytes split into lines
    a_lines = read_file_as_lines(a_path)
    b_lines = read_file_as_lines(b_path)
    
    # Check for read errors (exit code 2, print nothing to stdout)
    if a_lines is None or b_lines is None:
        print(f"Error: Could not read file(s)", file=sys.stderr)
        return 2
    
    # Execute the appropriate command
    if command == "lines":
        print_line_diff(a_lines, b_lines)
    else:  # highlight
        print_highlight_diff(a_lines, b_lines)
    
    return 0


# Entry point - raise SystemExit with return code from main()
raise SystemExit(main())
