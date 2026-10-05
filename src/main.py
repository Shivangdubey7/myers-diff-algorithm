"""Myers' O(ND) diff: line diff and changed-character ranges."""

import sys


def read_lines(path):
    with open(path, "rb") as f:
        lines = f.read().split(b"\n")
    if lines and not lines[-1]:
        lines.pop()
    return lines


def middle_snake(A, B, Ar, Br, n, m):
    delta = n - m
    odd = delta & 1
    max_d = (n + m + 1) // 2
    offset = max_d + 1
    size = 2 * max_d + 3
    vf = [-1] * size
    vb = [-1] * size
    vf[offset + 1] = vb[offset + 1] = 0
    fs = fe = bs = be = 0

    for d in range(max_d + 1):
        for k in range(-d + fs, d - fe + 1, 2):
            idx = offset + k
            x = vf[idx + 1] if k == -d or (k != d and vf[idx - 1] < vf[idx + 1]) else vf[idx - 1] + 1
            y = x - k
            x0, y0 = x, y
            while x < n and y < m and A[x] == B[y]:
                x += 1
                y += 1
            vf[idx] = x
            if x > n:
                fe += 2
                continue
            if y > m:
                fs += 2
                continue
            if odd:
                kb = delta - k
                if -d < kb < d:
                    xb = vb[offset + kb]
                    if xb != -1 and x + xb >= n:
                        return x0, y0, x, y

        for k in range(-d + bs, d - be + 1, 2):
            idx = offset + k
            x = vb[idx + 1] if k == -d or (k != d and vb[idx - 1] < vb[idx + 1]) else vb[idx - 1] + 1
            y = x - k
            x0, y0 = x, y
            while x < n and y < m and Ar[x] == Br[y]:
                x += 1
                y += 1
            vb[idx] = x
            if x > n:
                be += 2
                continue
            if y > m:
                bs += 2
                continue
            if not odd:
                kf = delta - k
                if -d <= kf <= d:
                    xf = vf[offset + kf]
                    if xf != -1 and xf + x >= n:
                        return n - x, m - y, n - x0, m - y0

    raise RuntimeError("middle snake not found")


def diff_marks(a, b):
    na, nb = len(a), len(b)
    ids, ia, ib = {}, [], []

    for item in a:
        if item not in ids:
            ids[item] = len(ids)
        ia.append(ids[item])

    for item in b:
        if item not in ids:
            ids[item] = len(ids)
        ib.append(ids[item])

    in_a, in_b = set(ia), set(ib)
    ma = [i for i, value in enumerate(ia) if value in in_b]
    mb = [j for j, value in enumerate(ib) if value in in_a]
    fa = [ia[i] for i in ma]
    fb = [ib[j] for j in mb]
    del_f, ins_f = bytearray(len(fa)), bytearray(len(fb))
    stack = [(0, len(fa), 0, len(fb))]

    while stack:
        a0, a1, b0, b1 = stack.pop()

        while a0 < a1 and b0 < b1 and fa[a0] == fb[b0]:
            a0 += 1
            b0 += 1
        while a0 < a1 and b0 < b1 and fa[a1 - 1] == fb[b1 - 1]:
            a1 -= 1
            b1 -= 1

        if a0 == a1:
            if b0 < b1:
                ins_f[b0:b1] = b"\x01" * (b1 - b0)
            continue
        if b0 == b1:
            del_f[a0:a1] = b"\x01" * (a1 - a0)
            continue

        A, B = fa[a0:a1], fb[b0:b1]
        n, m = a1 - a0, b1 - b0
        Ar, Br = A[::-1], B[::-1]
        A.append(-1)
        B.append(-2)
        Ar.append(-1)
        Br.append(-2)
        sx, sy, ex, ey = middle_snake(A, B, Ar, Br, n, m)

        stack.append((a0 + ex, a1, b0 + ey, b1))
        stack.append((a0, a0 + sx, b0, b0 + sy))

    del_a = bytearray(b"\x01") * na
    ins_b = bytearray(b"\x01") * nb
    for fi, oi in enumerate(ma):
        del_a[oi] = del_f[fi]
    for fi, oi in enumerate(mb):
        ins_b[oi] = ins_f[fi]
    return del_a, ins_b


def ranges(marks):
    n, parts = len(marks), []
    start = marks.find(1)
    while start != -1:
        end = marks.find(0, start)
        if end == -1:
            end = n
        parts.append(f"{start}-{end}")
        if end >= n:
            break
        start = marks.find(1, end)
    return ",".join(parts) if parts else "."


def build_output(a, b, del_a, ins_b, highlight):
    na, nb = len(a), len(b)
    out = []
    i = j = 0

    while True:
        next_delete, next_insert = del_a.find(1, i), ins_b.find(1, j)
        if next_delete == -1 and next_insert == -1:
            break

        count = na - i
        if next_delete != -1:
            count = min(count, next_delete - i)
        if next_insert != -1:
            count = min(count, next_insert - j)

        if count:
            out.extend(b" " + line for line in a[i:i + count])
            i += count
            j += count

        delete_end = del_a.find(0, i)
        insert_end = ins_b.find(0, j)
        if delete_end == -1:
            delete_end = na
        if insert_end == -1:
            insert_end = nb

        deleted, inserted = a[i:delete_end], b[j:insert_end]
        out.extend(b"-" + line for line in deleted)

        if not highlight:
            out.extend(b"+" + line for line in inserted)
        else:
            paired = min(len(deleted), len(inserted))
            for index, line in enumerate(inserted):
                out.append(b"+" + line)
                if index < paired:
                    old = deleted[index].decode("utf-8", "surrogateescape")
                    new = line.decode("utf-8", "surrogateescape")
                    deleted_marks, inserted_marks = diff_marks(old, new)
                    out.append(
                        f"? {ranges(deleted_marks)} | {ranges(inserted_marks)}".encode("utf-8")
                    )

        i, j = delete_end, insert_end

    if i < na:
        out.extend(b" " + line for line in a[i:])
    return out


def main():
    if len(sys.argv) != 4:
        print("usage: main.py lines|highlight A_PATH B_PATH", file=sys.stderr)
        return 2

    command = sys.argv[1]
    if command not in ("lines", "highlight"):
        print("usage: main.py lines|highlight A_PATH B_PATH", file=sys.stderr)
        return 2

    try:
        a, b = read_lines(sys.argv[2]), read_lines(sys.argv[3])
    except OSError as exc:
        print(f"error: cannot read file: {exc}", file=sys.stderr)
        return 2

    del_a, ins_b = diff_marks(a, b)
    output = build_output(a, b, del_a, ins_b, command == "highlight")

    if output:
        sys.stdout.buffer.write(b"\n".join(output) + b"\n")
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
