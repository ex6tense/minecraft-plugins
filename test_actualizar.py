import os
import tempfile

from actualizar import elegir, leer_lista, version_mc

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

    vh = os.path.join(d, "version_history.json")
    for texto, esperado in [("26.3-235-main@bb10cf0 (2026-10-01T00:00:00Z)", "26.3"),
                            ("git-Paper-196 (MC: 1.21.4)", "1.21.4"),
                            ("1.21.11-12-main@abc (x)", "1.21.11")]:
        with open(vh, "w") as f:
            f.write('{"currentVersion": "%s"}' % texto)
        assert version_mc(d) == esperado, texto
    os.remove(vh)
    assert version_mc(d) is None
    os.makedirs(os.path.join(d, "versions", "26.3"))
    open(os.path.join(d, "versions", "26.3", "paper-26.3.jar"), "w").close()
    assert version_mc(d) == "26.3"

print("ok")
