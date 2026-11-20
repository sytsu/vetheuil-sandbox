#!/usr/bin/env python3
"""vt new — emit a minimal iOS SwiftUI Xcode project without Xcode.

Writes <Name>.xcodeproj/project.pbxproj (objectVersion 77, one synchronized
root folder, so source files are picked up just by existing on disk) and a
shared scheme. Object IDs are deterministic (md5 of name+role), so
regenerating gives a zero diff.

usage: vt_new.py NAME BUNDLE_ID [--display-name "Name"] [--ios 17.0] [--out DIR]
"""
import argparse
import hashlib
import os
import re

SAFE = re.compile(r"^[A-Za-z0-9_$./]+$")


def q(value: str) -> str:
    """Quote a pbxproj string the way Xcode does."""
    if value and SAFE.match(value):
        return value
    esc = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{esc}"'


def oid(name: str, role: str) -> str:
    return hashlib.md5(f"{name}:{role}".encode()).hexdigest()[:24].upper()


def settings_block(d: dict, indent: str) -> str:
    lines = []
    for k in sorted(d):
        v = d[k]
        if isinstance(v, list):
            inner = "".join(f"{indent}\t{q(x)},\n" for x in v)
            lines.append(f"{indent}{k} = (\n{inner}{indent});\n")
        else:
            lines.append(f"{indent}{k} = {q(str(v))};\n")
    return "".join(lines)


def pbxproj(name: str, bundle_id: str, display: str, ios: str) -> str:
    I = {r: oid(name, r) for r in [
        "product", "syncgroup", "frameworks", "maingroup", "productsgroup",
        "target", "target_cfglist", "sources", "resources", "project",
        "project_cfglist", "proj_debug", "proj_release", "tgt_debug", "tgt_release",
    ]}
    common = {
        "ALWAYS_SEARCH_USER_PATHS": "NO",
        "ASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS": "YES",
        "CLANG_ENABLE_MODULES": "YES",
        "CLANG_ENABLE_OBJC_ARC": "YES",
        "COPY_PHASE_STRIP": "NO",
        "ENABLE_STRICT_OBJC_MSGSEND": "YES",
        "ENABLE_USER_SCRIPT_SANDBOXING": "YES",
        "GCC_C_LANGUAGE_STANDARD": "gnu17",
        "IPHONEOS_DEPLOYMENT_TARGET": ios,
        "LOCALIZATION_PREFERS_STRING_CATALOGS": "YES",
        "SDKROOT": "iphoneos",
    }
    proj_debug = {**common,
        "DEBUG_INFORMATION_FORMAT": "dwarf",
        "ENABLE_TESTABILITY": "YES",
        "GCC_OPTIMIZATION_LEVEL": "0",
        "GCC_PREPROCESSOR_DEFINITIONS": ["DEBUG=1", "$(inherited)"],
        "ONLY_ACTIVE_ARCH": "YES",
        "SWIFT_ACTIVE_COMPILATION_CONDITIONS": "DEBUG $(inherited)",
        "SWIFT_OPTIMIZATION_LEVEL": "-Onone",
    }
    proj_release = {**common,
        "DEBUG_INFORMATION_FORMAT": "dwarf-with-dsym",
        "ENABLE_NS_ASSERTIONS": "NO",
        "SWIFT_COMPILATION_MODE": "wholemodule",
        "VALIDATE_PRODUCT": "YES",
    }
    tgt = {
        "ASSETCATALOG_COMPILER_APPICON_NAME": "AppIcon",
        "ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME": "AccentColor",
        "CODE_SIGN_STYLE": "Automatic",
        "CURRENT_PROJECT_VERSION": "1",
        "GENERATE_INFOPLIST_FILE": "YES",
        "INFOPLIST_KEY_CFBundleDisplayName": display,
        "INFOPLIST_KEY_UIApplicationSceneManifest_Generation": "YES",
        "INFOPLIST_KEY_UIApplicationSupportsIndirectInputEvents": "YES",
        "INFOPLIST_KEY_UILaunchScreen_Generation": "YES",
        "INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone": "UIInterfaceOrientationPortrait",
        "LD_RUNPATH_SEARCH_PATHS": ["$(inherited)", "@executable_path/Frameworks"],
        "MARKETING_VERSION": "0.1",
        "PRODUCT_BUNDLE_IDENTIFIER": bundle_id,
        "PRODUCT_NAME": "$(TARGET_NAME)",
        "SWIFT_EMIT_LOC_STRINGS": "YES",
        "SWIFT_VERSION": "6.0",
        "TARGETED_DEVICE_FAMILY": "1",
    }
    T = "\t"

    def cfg(id_, nm, s):
        return (f"{T*2}{id_} /* {nm} */ = {{\n{T*3}isa = XCBuildConfiguration;\n"
                f"{T*3}buildSettings = {{\n{settings_block(s, T*4)}{T*3}}};\n"
                f"{T*3}name = {nm};\n{T*2}}};\n")

    def phase(id_, isa, nm):
        return (f"{T*2}{id_} /* {nm} */ = {{\n{T*3}isa = {isa};\n"
                f"{T*3}buildActionMask = 2147483647;\n{T*3}files = (\n{T*3});\n"
                f"{T*3}runOnlyForDeploymentPostprocessing = 0;\n{T*2}}};\n")

    app = f"{name}.app"
    return f"""// !$*UTF8*$!
{{
{T}archiveVersion = 1;
{T}classes = {{
{T}}};
{T}objectVersion = 77;
{T}objects = {{

/* Begin PBXFileReference section */
{T*2}{I['product']} /* {app} */ = {{isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = {q(app)}; sourceTree = BUILT_PRODUCTS_DIR; }};
/* End PBXFileReference section */

/* Begin PBXFileSystemSynchronizedRootGroup section */
{T*2}{I['syncgroup']} /* {name} */ = {{
{T*3}isa = PBXFileSystemSynchronizedRootGroup;
{T*3}path = {q(name)};
{T*3}sourceTree = "<group>";
{T*2}}};
/* End PBXFileSystemSynchronizedRootGroup section */

/* Begin PBXFrameworksBuildPhase section */
{phase(I['frameworks'], 'PBXFrameworksBuildPhase', 'Frameworks')}/* End PBXFrameworksBuildPhase section */

/* Begin PBXGroup section */
{T*2}{I['maingroup']} = {{
{T*3}isa = PBXGroup;
{T*3}children = (
{T*4}{I['syncgroup']} /* {name} */,
{T*4}{I['productsgroup']} /* Products */,
{T*3});
{T*3}sourceTree = "<group>";
{T*2}}};
{T*2}{I['productsgroup']} /* Products */ = {{
{T*3}isa = PBXGroup;
{T*3}children = (
{T*4}{I['product']} /* {app} */,
{T*3});
{T*3}name = Products;
{T*3}sourceTree = "<group>";
{T*2}}};
/* End PBXGroup section */

/* Begin PBXNativeTarget section */
{T*2}{I['target']} /* {name} */ = {{
{T*3}isa = PBXNativeTarget;
{T*3}buildConfigurationList = {I['target_cfglist']} /* Build configuration list for PBXNativeTarget "{name}" */;
{T*3}buildPhases = (
{T*4}{I['sources']} /* Sources */,
{T*4}{I['frameworks']} /* Frameworks */,
{T*4}{I['resources']} /* Resources */,
{T*3});
{T*3}buildRules = (
{T*3});
{T*3}dependencies = (
{T*3});
{T*3}fileSystemSynchronizedGroups = (
{T*4}{I['syncgroup']} /* {name} */,
{T*3});
{T*3}name = {q(name)};
{T*3}packageProductDependencies = (
{T*3});
{T*3}productName = {q(name)};
{T*3}productReference = {I['product']} /* {app} */;
{T*3}productType = "com.apple.product-type.application";
{T*2}}};
/* End PBXNativeTarget section */

/* Begin PBXProject section */
{T*2}{I['project']} /* Project object */ = {{
{T*3}isa = PBXProject;
{T*3}attributes = {{
{T*4}BuildIndependentTargetsInParallel = 1;
{T*4}LastSwiftUpdateCheck = 2600;
{T*4}LastUpgradeCheck = 2600;
{T*4}TargetAttributes = {{
{T*5}{I['target']} = {{
{T*6}CreatedOnToolsVersion = 26.0;
{T*5}}};
{T*4}}};
{T*3}}};
{T*3}buildConfigurationList = {I['project_cfglist']} /* Build configuration list for PBXProject "{name}" */;
{T*3}developmentRegion = en;
{T*3}hasScannedForEncodings = 0;
{T*3}knownRegions = (
{T*4}en,
{T*4}Base,
{T*3});
{T*3}mainGroup = {I['maingroup']};
{T*3}minimizedProjectReferenceProxies = 1;
{T*3}preferredProjectObjectVersion = 77;
{T*3}productRefGroup = {I['productsgroup']} /* Products */;
{T*3}projectDirPath = "";
{T*3}projectRoot = "";
{T*3}targets = (
{T*4}{I['target']} /* {name} */,
{T*3});
{T*2}}};
/* End PBXProject section */

/* Begin PBXResourcesBuildPhase section */
{phase(I['resources'], 'PBXResourcesBuildPhase', 'Resources')}/* End PBXResourcesBuildPhase section */

/* Begin PBXSourcesBuildPhase section */
{phase(I['sources'], 'PBXSourcesBuildPhase', 'Sources')}/* End PBXSourcesBuildPhase section */

/* Begin XCBuildConfiguration section */
{cfg(I['proj_debug'], 'Debug', proj_debug)}{cfg(I['proj_release'], 'Release', proj_release)}{cfg(I['tgt_debug'], 'Debug', tgt)}{cfg(I['tgt_release'], 'Release', tgt)}/* End XCBuildConfiguration section */

/* Begin XCConfigurationList section */
{T*2}{I['project_cfglist']} /* Build configuration list for PBXProject "{name}" */ = {{
{T*3}isa = XCConfigurationList;
{T*3}buildConfigurations = (
{T*4}{I['proj_debug']} /* Debug */,
{T*4}{I['proj_release']} /* Release */,
{T*3});
{T*3}defaultConfigurationIsVisible = 0;
{T*3}defaultConfigurationName = Release;
{T*2}}};
{T*2}{I['target_cfglist']} /* Build configuration list for PBXNativeTarget "{name}" */ = {{
{T*3}isa = XCConfigurationList;
{T*3}buildConfigurations = (
{T*4}{I['tgt_debug']} /* Debug */,
{T*4}{I['tgt_release']} /* Release */,
{T*3});
{T*3}defaultConfigurationIsVisible = 0;
{T*3}defaultConfigurationName = Release;
{T*2}}};
/* End XCConfigurationList section */
{T}}};
{T}rootObject = {I['project']} /* Project object */;
}}
""", I


def scheme(name: str, target_id: str) -> str:
    ref = (f'BuildableIdentifier = "primary" BlueprintIdentifier = "{target_id}" '
           f'BuildableName = "{name}.app" BlueprintName = "{name}" '
           f'ReferencedContainer = "container:{name}.xcodeproj"')
    lldb = ('selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB" '
            'selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Scheme
   LastUpgradeVersion = "2600"
   version = "1.7">
   <BuildAction
      parallelizeBuildables = "YES"
      buildImplicitDependencies = "YES">
      <BuildActionEntries>
         <BuildActionEntry
            buildForTesting = "YES"
            buildForRunning = "YES"
            buildForProfiling = "YES"
            buildForArchiving = "YES"
            buildForAnalyzing = "YES">
            <BuildableReference {ref}>
            </BuildableReference>
         </BuildActionEntry>
      </BuildActionEntries>
   </BuildAction>
   <TestAction
      buildConfiguration = "Debug" {lldb}
      shouldUseLaunchSchemeArgsEnv = "YES"
      shouldAutocreateTestPlan = "YES">
   </TestAction>
   <LaunchAction
      buildConfiguration = "Debug" {lldb}
      launchStyle = "0"
      useCustomWorkingDirectory = "NO"
      ignoresPersistentStateOnLaunch = "NO"
      debugDocumentVersioning = "YES"
      debugServiceExtension = "internal"
      allowLocationSimulation = "YES">
      <BuildableProductRunnable
         runnableDebuggingMode = "0">
         <BuildableReference {ref}>
         </BuildableReference>
      </BuildableProductRunnable>
   </LaunchAction>
   <ProfileAction
      buildConfiguration = "Release"
      shouldUseLaunchSchemeArgsEnv = "YES"
      savedToolIdentifier = ""
      useCustomWorkingDirectory = "NO"
      debugDocumentVersioning = "YES">
      <BuildableProductRunnable
         runnableDebuggingMode = "0">
         <BuildableReference {ref}>
         </BuildableReference>
      </BuildableProductRunnable>
   </ProfileAction>
   <AnalyzeAction
      buildConfiguration = "Debug">
   </AnalyzeAction>
   <ArchiveAction
      buildConfiguration = "Release"
      revealArchiveInOrganizer = "YES">
   </ArchiveAction>
</Scheme>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("bundle_id")
    ap.add_argument("--display-name")
    ap.add_argument("--ios", default="17.0")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    text, ids = pbxproj(a.name, a.bundle_id, a.display_name or a.name, a.ios)
    proj = os.path.join(a.out, f"{a.name}.xcodeproj")
    os.makedirs(os.path.join(proj, "xcshareddata", "xcschemes"), exist_ok=True)
    with open(os.path.join(proj, "project.pbxproj"), "w", encoding="utf-8") as f:
        f.write(text)
    with open(os.path.join(proj, "xcshareddata", "xcschemes", f"{a.name}.xcscheme"), "w", encoding="utf-8") as f:
        f.write(scheme(a.name, ids["target"]))
    os.makedirs(os.path.join(a.out, a.name), exist_ok=True)
    print(f"wrote {proj}")


if __name__ == "__main__":
    main()
