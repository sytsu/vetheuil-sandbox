#!/usr/bin/env python3
"""vt validate — structural checks for an Xcode project, no Xcode needed.

Checks: pbxproj parses; every object has an isa; every referenced object ID
exists; on-disk paths for synchronized folders and file references exist;
shared schemes point at real targets; asset-catalog Contents.json files parse
and their images exist; plists/entitlements parse. Lists every shell
script build phase so new or changed scripts can't slip in unnoticed.

usage: vt_validate.py [PROJECT.xcodeproj]   (exit 1 on errors)
"""
import glob
import hashlib
import json
import os
import plistlib
import re
import sys
import xml.etree.ElementTree as ET

ID = re.compile(r"^[0-9A-F]{24}$")


class ParseError(Exception):
    pass


def parse_openstep(text: str):
    """Minimal parser for Xcode's old-style (OpenStep) plist."""
    i, n = 0, len(text)

    def skip():
        nonlocal i
        while i < n:
            c = text[i]
            if c in " \t\r\n":
                i += 1
            elif text.startswith("//", i):
                j = text.find("\n", i)
                i = n if j < 0 else j + 1
            elif text.startswith("/*", i):
                j = text.find("*/", i + 2)
                if j < 0:
                    raise ParseError("unterminated comment")
                i = j + 2
            else:
                break

    def value():
        nonlocal i
        skip()
        if i >= n:
            raise ParseError("unexpected end of file")
        c = text[i]
        if c == "{":
            i += 1
            d = {}
            while True:
                skip()
                if text[i] == "}":
                    i += 1
                    return d
                k = value()
                skip()
                if text[i] != "=":
                    raise ParseError(f"expected '=' at offset {i}")
                i += 1
                d[k] = value()
                skip()
                if text[i] != ";":
                    raise ParseError(f"expected ';' at offset {i}")
                i += 1
        if c == "(":
            i += 1
            arr = []
            while True:
                skip()
                if text[i] == ")":
                    i += 1
                    return arr
                arr.append(value())
                skip()
                if text[i] == ",":
                    i += 1
                elif text[i] != ")":
                    raise ParseError(f"expected ',' or ')' at offset {i}")
        if c == '"':
            i += 1
            out = []
            while text[i] != '"':
                if text[i] == "\\":
                    i += 1
                    out.append({"n": "\n", "t": "\t"}.get(text[i], text[i]))
                else:
                    out.append(text[i])
                i += 1
            i += 1
            return "".join(out)
        m = re.compile(r"[^\s;,=(){}\"]+").match(text, i)
        if not m:
            raise ParseError(f"unexpected character {c!r} at offset {i}")
        i = m.end()
        return m.group(0)

    result = value()
    skip()
    if i != n:
        raise ParseError(f"trailing content at offset {i}")
    return result


def walk_ids(v, out):
    if isinstance(v, str):
        if ID.match(v):
            out.add(v)
    elif isinstance(v, list):
        for x in v:
            walk_ids(x, out)
    elif isinstance(v, dict):
        for k, x in v.items():
            walk_ids(k, out)
            walk_ids(x, out)


def main():
    args = sys.argv[1:]
    projs = args or glob.glob("*.xcodeproj")
    if not projs:
        print("no .xcodeproj found")
        return 1
    errors, warnings, notes = [], [], []
    for proj in projs:
        root = os.path.dirname(os.path.abspath(proj))
        pbx = os.path.join(proj, "project.pbxproj")
        if not os.path.exists(pbx):
            if os.path.exists(os.path.join(proj, "project.xcproj")):
                notes.append(f"{proj}: JSON .xcproj format, not checked yet")
                continue
            errors.append(f"{proj}: no project.pbxproj")
            continue
        try:
            data = parse_openstep(open(pbx, encoding="utf-8").read())
        except (ParseError, IndexError) as e:
            errors.append(f"{pbx}: parse error: {e}")
            continue
        objs = data.get("objects", {})
        if data.get("rootObject") not in objs:
            errors.append(f"{pbx}: rootObject missing")
        refs = set()
        for oid, o in objs.items():
            if "isa" not in o:
                errors.append(f"{pbx}: object {oid} has no isa")
            walk_ids({k: v for k, v in o.items()}, refs)
        walk_ids(data.get("rootObject"), refs)
        for r in sorted(refs - set(objs)):
            errors.append(f"{pbx}: dangling reference {r}")
        targets = {oid: o for oid, o in objs.items()
                   if o.get("isa") in ("PBXNativeTarget", "PBXAggregateTarget", "PBXLegacyTarget")}
        parent = {}
        for gid, g in objs.items():
            for child in g.get("children", []) if isinstance(g.get("children"), list) else []:
                parent[child] = gid

        def disk_path(oid_):
            """Resolve a group-relative path by walking up the group chain."""
            parts, cur = [], oid_
            while cur in objs:
                o_ = objs[cur]
                tree = o_.get("sourceTree", "<group>")
                if o_.get("path"):
                    parts.append(o_["path"])
                if tree == "SOURCE_ROOT":
                    break
                if tree != "<group>":
                    return None  # BUILT_PRODUCTS_DIR, SDKROOT, absolute, ...
                cur = parent.get(cur)
            return os.path.join(root, *reversed(parts))

        for oid, o in objs.items():
            isa = o.get("isa")
            if isa == "PBXFileSystemSynchronizedRootGroup":
                p = disk_path(oid)
                if p and not os.path.isdir(p):
                    errors.append(f"{pbx}: synchronized folder missing on disk: {os.path.relpath(p, root)}")
            elif isa == "PBXFileReference":
                p = disk_path(oid)
                if p and not os.path.exists(p):
                    warnings.append(f"{pbx}: file reference not on disk: {os.path.relpath(p, root)}")
            elif isa == "PBXShellScriptBuildPhase":
                script = o.get("shellScript", "")
                h = hashlib.sha256(script.encode()).hexdigest()[:12]
                warnings.append(f"{pbx}: shell script phase {o.get('name', oid)} sha256:{h} — review it")
        # schemes
        for sch in glob.glob(os.path.join(proj, "xcshareddata", "xcschemes", "*.xcscheme")):
            try:
                tree = ET.parse(sch)
            except ET.ParseError as e:
                errors.append(f"{sch}: XML error: {e}")
                continue
            for br in tree.iter("BuildableReference"):
                bid = br.get("BlueprintIdentifier")
                cont = br.get("ReferencedContainer", "")
                if cont == f"container:{os.path.basename(proj)}" and bid not in targets:
                    warnings.append(f"{os.path.basename(sch)}: stale reference to missing target "
                                    f"{br.get('BlueprintName', bid)} ({bid})")
        notes.append(f"{proj}: {len(objs)} objects, {len(targets)} target(s): "
                     + ", ".join(t.get("name", "?") for t in targets.values()))

    # asset catalogs, plists, entitlements anywhere in the repo
    for cj in glob.glob("**/*.xcassets/**/Contents.json", recursive=True):
        try:
            d = json.load(open(cj, encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{cj}: JSON error: {e}")
            continue
        for img in d.get("images", []):
            fn = img.get("filename")
            if fn and not os.path.exists(os.path.join(os.path.dirname(cj), fn)):
                errors.append(f"{cj}: missing image {fn}")
    for pl in glob.glob("**/*.plist", recursive=True) + glob.glob("**/*.entitlements", recursive=True):
        if "/build/" in pl or pl.startswith("build/"):
            continue
        try:
            plistlib.load(open(pl, "rb"))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{pl}: plist error: {e}")

    for n_ in notes:
        print("ok   ", n_)
    for w in warnings:
        print("warn ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
