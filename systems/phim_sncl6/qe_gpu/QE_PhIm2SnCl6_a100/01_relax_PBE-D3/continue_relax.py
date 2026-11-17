"""Write a new relax input that starts from the last geometry printed in an interrupted pw.x output."""
import sys, re
out, template, new = sys.argv[1:4]
txt = open(out).read()
blocks = re.findall(r"ATOMIC_POSITIONS \(crystal\)\n(.*?)\n\n", txt, re.S)
if not blocks:
    sys.exit("no ATOMIC_POSITIONS block found in " + out)
last = [l for l in blocks[-1].splitlines() if l.strip() and not l.startswith("End")]
tpl = open(template).read()
head, rest = tpl.split("ATOMIC_POSITIONS crystal\n")
nat = len([l for l in rest.split("K_POINTS")[0].splitlines() if l.strip()])
assert len(last) == nat, (len(last), nat)
tail = "K_POINTS" + rest.split("K_POINTS", 1)[1]
open(new, "w").write(head + "ATOMIC_POSITIONS crystal\n" + "\n".join("  " + l.strip() for l in last) + "\n" + tail)
print(f"wrote {new} from step {len(blocks)} of {out}")
