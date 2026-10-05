import sys


def read_lines(path):
    # Read raw bytes, split on newline byte, drop final empty piece.
    # Keeps any \r inside the line. Empty file -> [].
    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception:
        return None
    parts = data.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return parts


def myers(a, b):
    # Myers O(ND) shortest edit script for any two sequences.
    # Edit graph: right = delete from a, down = insert from b,
    # diagonal = keep (free). k = x - y is the diagonal.
    # V[k] = furthest x reached on diagonal k.
    # A snake follows matching items diagonally for free.
    # First d that reaches (n, m) is minimal D.
    n = len(a)
    m = len(b)
    # Common prefix: these are keeps, skip them.
    p = 0
    while p < n and p < m and a[p] == b[p]:
        p += 1
    # Common suffix: also keeps.
    s = 0
    while s < n - p and s < m - p and a[n - 1 - s] == b[m - 1 - s]:
        s += 1
    # Middle part that really differs.
    if s:
        amid = a[p:n - s]
        bmid = b[p:m - s]
    else:
        amid = a[p:]
        bmid = b[p:]
    na = len(amid)
    nb = len(bmid)
    if na == 0 and nb == 0:
        mid = []
    elif na == 0:
        mid = []
        for j in range(nb):
            mid.append(("insert", 0, j))
    elif nb == 0:
        mid = []
        for i in range(na):
            mid.append(("delete", i, 0))
    elif amid == bmid:
        mid = []
        for i in range(na):
            mid.append(("keep", i, i))
    else:
        mid = myers_core(amid, bmid)
    # Stitch prefix keeps + middle + suffix keeps with global indexes.
    # Optimize: don't materialize all prefix/suffix keeps - use range markers
    out = []
    if p > 0:
        out.append(("keep_range", 0, 0, p))  # keep lines 0..p-1
    for op, ai, bi in mid:
        if op == "keep":
            out.append(("keep", p + ai, p + bi))
        elif op == "delete":
            out.append(("delete", p + ai, 0))
        else:
            out.append(("insert", 0, p + bi))
    if s > 0:
        out.append(("keep_range", n - s, m - s, s))  # keep s lines at end
    return out


def myers_core(a, b):
    # Core forward Myers on the trimmed middle. Returns edit script.
    n = len(a)
    m = len(b)
    max_d = n + m
    offset = max_d
    size = 2 * max_d + 1
    
    v = [0] * size
    # Store only visited k values per depth (sparse storage)
    history = [{}]
    
    for d in range(max_d + 1):
        snap = {}
        
        for k in range(-d, d + 1, 2):
            idx = k + offset
            
            if k == -d or (k != d and v[idx - 1] < v[idx + 1]):
                x = v[idx + 1]
            else:
                x = v[idx - 1] + 1
            
            y = x - k
            
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1
            
            v[idx] = x
            snap[k] = x
            
            if x == n and y == m:
                history.append(snap)
                result = backtrack(history, a, b, d, offset)
                del history  # Free memory immediately
                return result
        
        history.append(snap)
    
    return []


def backtrack(history, a, b, d, offset):
    # Walk backwards from (n, m) using saved V dictionaries.
    n = len(a)
    m = len(b)
    x = n
    y = m
    rev = []
    
    for depth in range(d, -1, -1):
        v = history[depth]
        k = x - y
        
        if k == -depth or (k != depth and v.get(k - 1, -1) < v.get(k + 1, -1)):
            prev_k = k + 1
        else:
            prev_k = k - 1
        
        prev_x = v.get(prev_k, 0)
        prev_y = prev_x - prev_k
        
        # Snake part = keeps.
        while x > prev_x and y > prev_y:
            x -= 1
            y -= 1
            rev.append(("keep", x, y))
        
        if depth > 0:
            if x == prev_x:
                y -= 1
                rev.append(("insert", x, y))
            else:
                x -= 1
                rev.append(("delete", x, y))
    
    rev.reverse()
    return rev


def build_lines(a_lines, b_lines):
    # Part A with delete-first rule. Write output incrementally.
    script = myers(a_lines, b_lines)
    dels = []
    inss = []

    def flush():
        if dels:
            for t in dels:
                sys.stdout.buffer.write(b"-")
                sys.stdout.buffer.write(t)
                sys.stdout.buffer.write(b"\n")
            dels.clear()
        if inss:
            for t in inss:
                sys.stdout.buffer.write(b"+")
                sys.stdout.buffer.write(t)
                sys.stdout.buffer.write(b"\n")
            inss.clear()

    for item in script:
        op = item[0]
        if op == "keep_range":
            if dels or inss:
                flush()
            # Write range of keep lines
            start_a = item[1]
            count = item[3]
            for i in range(count):
                sys.stdout.buffer.write(b" ")
                sys.stdout.buffer.write(a_lines[start_a + i])
                sys.stdout.buffer.write(b"\n")
        elif op == "keep":
            if dels or inss:
                flush()
            sys.stdout.buffer.write(b" ")
            sys.stdout.buffer.write(a_lines[item[1]])
            sys.stdout.buffer.write(b"\n")
        elif op == "delete":
            dels.append(a_lines[item[1]])
        else:  # insert
            inss.append(b_lines[item[2]])
    if dels or inss:
        flush()


def ranges_of(pos):
    # pos = sorted changed indexes -> "s-e,s-e" or "." Merges touching.
    if not pos:
        return "."
    pos = sorted(pos)
    parts = []
    s = pos[0]
    e = pos[0] + 1
    for q in pos[1:]:
        if q == e:
            e = q + 1
        else:
            parts.append(str(s) + "-" + str(e))
            s = q
            e = q + 1
    parts.append(str(s) + "-" + str(e))
    return ",".join(parts)


def char_ranges(old_b, new_b):
    # Myers on characters. Counts Unicode code points, not bytes.
    old_s = old_b.decode("utf-8")
    new_s = new_b.decode("utf-8")
    oc = list(old_s)
    nc = list(new_s)
    script = myers(oc, nc)
    op_ = []
    np_ = []
    for item in script:
        op = item[0]
        if op == "delete":
            op_.append(item[1])
        elif op == "insert":
            np_.append(item[2])
        # keep_range doesn't produce changes, skip it
    return ranges_of(op_), ranges_of(np_)


def build_highlight(a_lines, b_lines):
    # Part B: same blocks as Part A, plus "? old | new" after each paired +.
    script = myers(a_lines, b_lines)
    dels = []
    inss = []

    def flush():
        if dels:
            for t in dels:
                sys.stdout.buffer.write(b"-")
                sys.stdout.buffer.write(t)
                sys.stdout.buffer.write(b"\n")
        if inss:
            for i, t in enumerate(inss):
                sys.stdout.buffer.write(b"+")
                sys.stdout.buffer.write(t)
                sys.stdout.buffer.write(b"\n")
                if i < len(dels):
                    o, w = char_ranges(dels[i], t)
                    sys.stdout.buffer.write(("? " + o + " | " + w + "\n").encode("utf-8"))
        dels.clear()
        inss.clear()

    for item in script:
        op = item[0]
        if op == "keep_range":
            if dels or inss:
                flush()
            # Write range of keep lines
            start_a = item[1]
            count = item[3]
            for i in range(count):
                sys.stdout.buffer.write(b" ")
                sys.stdout.buffer.write(a_lines[start_a + i])
                sys.stdout.buffer.write(b"\n")
        elif op == "keep":
            if dels or inss:
                flush()
            sys.stdout.buffer.write(b" ")
            sys.stdout.buffer.write(a_lines[item[1]])
            sys.stdout.buffer.write(b"\n")
        elif op == "delete":
            dels.append(a_lines[item[1]])
        else:  # insert
            inss.append(b_lines[item[2]])
    if dels or inss:
        flush()


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A B", file=sys.stderr)
        return 2
    cmd = sys.argv[1]
    a = read_lines(sys.argv[2])
    b = read_lines(sys.argv[3])
    if a is None or b is None:
        print("Error: cannot read file", file=sys.stderr)
        return 2
    if cmd == "lines":
        build_lines(a, b)
    else:
        build_highlight(a, b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
