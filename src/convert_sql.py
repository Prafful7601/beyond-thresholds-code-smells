"""Convert the DACOS MySQL dumps to SQLite without a MySQL server.

Usage: python -I src/convert_sql.py <dump.sql> <out.sqlite>

Parses CREATE TABLE blocks for column names and tokenises every
`INSERT INTO ... VALUES (...),(...);` statement byte by byte, honouring MySQL
string escapes. `bit(1)` columns are dumped as `_binary '<byte>'`; they are
stored as the integer value of that byte (0 or 1). Everything else is kept as
the literal text MySQL wrote (numbers as stored strings for varchar columns),
so no values are coerced at this stage.
"""
import re
import sqlite3
import sys

ESC = {b"0": b"\0", b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b",
       b"Z": b"\x1a", b"\\": b"\\", b"'": b"'", b'"': b'"'}


def parse_create(sql):
    tables = {}
    for m in re.finditer(rb"CREATE TABLE `([^`]+)` \((.*?)\n\) ENGINE", sql, re.S):
        cols, types = [], []
        for line in m.group(2).split(b"\n"):
            cm = re.match(rb"\s*`([^`]+)` (\w+)", line)
            if cm:
                cols.append(cm.group(1).decode())
                types.append(cm.group(2).decode().lower())
        tables[m.group(1).decode()] = (cols, types)
    return tables


def parse_values(buf, i):
    """Yield row tuples from buf starting at index i (just after VALUES)."""
    n = len(buf)
    while i < n:
        c = buf[i:i + 1]
        if c == b"(":
            i += 1
            row = []
            while True:
                while buf[i:i + 1] in (b" ", b"\n"):
                    i += 1
                is_bin = False
                if buf.startswith(b"_binary ", i):
                    is_bin = True
                    i += 8
                if buf[i:i + 1] == b"'":
                    i += 1
                    out = bytearray()
                    while True:
                        ch = buf[i:i + 1]
                        if ch == b"\\":
                            nxt = buf[i + 1:i + 2]
                            out += ESC.get(nxt, nxt)
                            i += 2
                        elif ch == b"'":
                            if buf[i + 1:i + 2] == b"'":
                                out += b"'"
                                i += 2
                            else:
                                i += 1
                                break
                        else:
                            out += ch
                            i += 1
                    if is_bin:
                        row.append(int.from_bytes(bytes(out), "big") if out else 0)
                    else:
                        row.append(bytes(out).decode("utf-8"))
                else:
                    j = i
                    while buf[j:j + 1] not in (b",", b")"):
                        j += 1
                    tok = buf[i:j].decode()
                    i = j
                    if tok == "NULL":
                        row.append(None)
                    elif re.fullmatch(r"-?\d+", tok):
                        row.append(int(tok))
                    else:
                        row.append(float(tok))
                if buf[i:i + 1] == b",":
                    i += 1
                    continue
                assert buf[i:i + 1] == b")", (i, buf[i:i + 40])
                i += 1
                yield tuple(row)
                break
        elif c == b",":
            i += 1
        elif c == b";":
            return
        else:
            raise ValueError("unexpected byte %r at %d" % (c, i))


def main(src, dst):
    sql = open(src, "rb").read()
    tables = parse_create(sql)
    con = sqlite3.connect(dst)
    for t, (cols, types) in tables.items():
        con.execute('DROP TABLE IF EXISTS "%s"' % t)
        decl = ", ".join('"%s" %s' % (c, "INTEGER" if ty in ("bigint", "int", "bit") else "TEXT")
                         for c, ty in zip(cols, types))
        con.execute('CREATE TABLE "%s" (%s)' % (t, decl))
    counts = {t: 0 for t in tables}
    for m in re.finditer(rb"INSERT INTO `([^`]+)` VALUES ", sql):
        t = m.group(1).decode()
        cols = tables[t][0]
        ph = ",".join("?" * len(cols))
        rows = list(parse_values(sql, m.end()))
        for r in rows:
            assert len(r) == len(cols), (t, r)
        con.executemany('INSERT INTO "%s" VALUES (%s)' % (t, ph), rows)
        counts[t] += len(rows)
    con.commit()
    for t, n in counts.items():
        print("%s\t%s\t%d rows" % (dst, t, n))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
