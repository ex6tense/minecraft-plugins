import os
import tempfile

from actualizar import elegir, leer_lista

vs = [
    {"version_number": "3", "game_versions": ["26.2"]},
    {"version_number": "2", "game_versions": ["26.3"]},
    {"version_number": "1", "game_versions": ["1.21.11"]},
]
assert elegir(vs, "26.3") == (vs[1], True)
assert elegir(vs[:1] + vs[2:], "26.3") == (vs[0], False)
assert elegir(vs[2:], "26.3") == (None, False)

with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "plugins.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("# comentario\n\ntpaa  TPA-*.jar ProTPA*.jar  # nota\n# gsit gsit*.jar\n")
    assert list(leer_lista(p)) == [("tpaa", ["tpa-*.jar", "protpa*.jar"])]

print("ok")
