#!/usr/bin/env python3
"""Print ten chunks of a text file as notice annotations, starting at chunk N."""
import sys

CHUNK = 3600  # an annotation keeps 4096 bytes
lines = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
chunks, current = [], ""
for line in lines:
    if current and len((current + line).encode("utf-8")) + 1 > CHUNK:
        chunks.append(current)
        current = ""
    current += line[:CHUNK] + "\n"
if current:
    chunks.append(current)
first = int(sys.argv[2])
for index in range(first, min(first + 10, len(chunks))):
    body = chunks[index].replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print("::notice title=report %03d of %03d::%s" % (index + 1, len(chunks), body))
if first == 0:
    print("%d chunks, %d characters" % (len(chunks), sum(map(len, chunks))))
