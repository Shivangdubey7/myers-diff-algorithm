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
        mid = [("insert", 0, j) for j in range(nb)]
    elif nb == 0:
        mid = [("delete", i, 0) for i in range(na)]
    elif amid == bmid:
        mid = [("keep", i, i) for i in range(na)]
    else:
        mid = myers_core(amid, bmid)
    # Stitch prefix keeps + middle + suffix keeps with global indexes.
    out = []
    for i in range(p):
        out.append(("keep", i, i))
    for op, ai, bi in mid:
        if op == "keep":
            out.append(("keep", p + ai, p + bi))
        elif op == "delete":
            out.append(("delete", p + ai, 0))
        else:
            out.append(("insert", 0, p + bi))
    for k in range(s):
        out.append(("keep", n - s + k, m - s + k))
    return out


def myers_core(a, b):
    # Core forward Myers on the trimmed middle. Returns edit script.
    n = len(a)
    m = len(b)
    max_d = n + m
    # Use array instead of dict: v_arr[k + offset] = x
    # offset shifts k into positive indices
    offset = max_d
    # Pre-allocate array for 2 depths (current and previous)
    v_size = 2 * max_d + 1
    v = [0] * v_size
    # Store only endpoints for backtracking: history[d][k] = x
    # Use dict per depth to save memory (only store visited k values)
    history = [{}]
    
    for d in range(max_d + 1):
        snap = {}
        # k runs -d..d step 2.
        for k in range(-d, d + 1, 2):
            k_idx = k + offset
            if k == -d or (k != d and v[k_idx - 1] < v[k_idx + 1]):
                # Down: insert from b, came from k+1.
                x = v[k_idx + 1]
            else:
                # Right: delete from a, came from k-1.
                x = v[k_idx - 1] + 1
            y = x - k
            # Snake: follow equal items.
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1
            v[k_idx] = x
            snap[k] = x
            if x == n and y == m:
                history.append(snap)
                return backtrack(history, a, b, d)
        history.append(snap)
    return []


def backtrack(history, a, b, d):
    # Walk backwards from (n, m) using saved V tables.
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
    # Part A with delete-first rule. Buffer output, write once.
    script = myers(a_lines, b_lines)
    buf = []
    dels = []
    inss = []

    def flush():
        for t in dels:
            buf.append(b"-" + t + b"\n")
        for t in inss:
            buf.append(b"+" + t + b"\n")
        dels.clear()
        inss.clear()

    for op, ai, bi in script:
        if op == "keep":
            if dels or inss:
                flush()
            buf.append(b" " + a_lines[ai] + b"\n")
        elif op == "delete":
            dels.append(a_lines[ai])
        else:
            inss.append(b_lines[bi])
    if dels or inss:
        flush()
    if buf:
        sys.stdout.buffer.write(b"".join(buf))


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
    for op, ai, bi in script:
        if op == "delete":
            op_.append(ai)
        elif op == "insert":
            np_.append(bi)
    return ranges_of(op_), ranges_of(np_)


def build_highlight(a_lines, b_lines):
    # Part B: same blocks as Part A, plus "? old | new" after each paired +.
    script = myers(a_lines, b_lines)
    buf = []
    dels = []
    inss = []

    def flush():
        for t in dels:
            buf.append(b"-" + t + b"\n")
        for i, t in enumerate(inss):
            buf.append(b"+" + t + b"\n")
            if i < len(dels):
                o, w = char_ranges(dels[i], t)
                buf.append(("? " + o + " | " + w + "\n").encode("utf-8"))
        dels.clear()
        inss.clear()

    for op, ai, bi in script:
        if op == "keep":
            if dels or inss:
                flush()
            buf.append(b" " + a_lines[ai] + b"\n")
        elif op == "delete":
            dels.append(a_lines[ai])
        else:
            inss.append(b_lines[bi])
    if dels or inss:
        flush()
    if buf:
        sys.stdout.buffer.write(b"".join(buf))


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
