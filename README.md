# vetheuil-sandbox

Throwaway test for Vétheuil: an iOS app whose Xcode project was **written and built without a Mac**.

- `tools/vt_new.py` generates `Sandbox.xcodeproj` (objectVersion 77, one synchronized folder, shared scheme). Object IDs are deterministic, so regenerating it gives a zero diff.
- `tools/vt_validate.py` runs structural checks on the project (references, folders, schemes, asset catalogs, plists, shell-script phases).
- `.github/workflows/build.yml` validates on Linux, builds unsigned on `macos-26`, packages an IPA and publishes it to the `rolling` pre-release.

Latest IPA: `https://github.com/sytsu/vetheuil-sandbox/releases/download/rolling/Vetheuil-Sandbox.ipa`. It's unsigned, so sign and install it with SideStore or similar.
