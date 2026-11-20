# vetheuil-sandbox

Throwaway test app for [Vétheuil](https://github.com/sytsu/vetheuil). Its Xcode project was written and built without a Mac.

- `Sandbox.xcodeproj` was generated on Linux (objectVersion 77, one synchronized folder, shared scheme).
- `.github/workflows/vetheuil.yml` was written by `vt init-ci`, then edited by hand to add a build-info stamp and keep the IPA's file name stable.
- Every push to `main` publishes an unsigned IPA here: `https://github.com/sytsu/vetheuil-sandbox/releases/download/rolling/Vetheuil-Sandbox.ipa`. Sign and install it with SideStore or similar.
