import os
import sys
from .._pkg_meta import  scan_for_metadata

def check(cmd, mf):
    infos = scan_for_metadata(sys.path)

    for m in mf.flatten():
        fn = getattr(m, "filename", None)
        meta = infos.get(fn, None)
        if meta is None:
            continue

        with open(os.path.join(meta, "top_level.txt"), "r") as fp:
            toplevels = []
            for line in fp:
                toplevels.append(line[:-1])

        for tl in toplevels:
            if tl.endswith("__mypyc"):
                # Package is compiled with mypyc
                break
        else:
            continue

        # Look
