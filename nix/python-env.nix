# Builds the python environment logsmith runs in.
#
# The dependencies come from `uv.lock` via uv2nix, so nix and `uv sync` install
# exactly the same versions. The result is a python interpreter that already
# knows about all runtime dependencies and about the Qt shipped inside the PyQt6
# wheels.
{
  pkgs,
  python,
  workspaceRoot,
  uv2nix,
  pyproject-nix,
  pyproject-build-systems,
}:
let
  inherit (pkgs) lib;

  workspace = uv2nix.lib.workspace.loadWorkspace { inherit workspaceRoot; };

  # The PyQt6 wheels bundle their own Qt build, so nixpkgs' Qt must never end up
  # on the library path - mixing the two causes symbol lookup errors. Only the
  # plain system libraries the bundled Qt links against are needed.
  qtSystemLibs = with pkgs; [
    dbus
    expat
    fontconfig
    freetype
    glib
    libglvnd
    libx11
    libxcb
    libxext
    libxkbcommon
    xcbutil
    xcbutilcursor
    xcbutilimage
    xcbutilkeysyms
    xcbutilrenderutil
    xcbutilwm
    zlib
    zstd
  ];

  # The prebuilt PyQt6 binaries link against Qt libraries shipped in the
  # separate pyqt6-qt6 wheel, which autoPatchelf cannot see at build time.
  withBundledQt =
    drv:
    drv.overrideAttrs (old: {
      autoPatchelfIgnoreMissingDeps = true;
      buildInputs = (old.buildInputs or [ ]) ++ qtSystemLibs;
    });

  pyqtOverlay = _final: prev: {
    pyqt6 = withBundledQt prev.pyqt6;
    pyqt6-qt6 = withBundledQt prev.pyqt6-qt6;
  };

  pythonSet = (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope (
    lib.composeManyExtensions [
      pyproject-build-systems.overlays.default
      (workspace.mkPyprojectOverlay { sourcePreference = "wheel"; })
      pyqtOverlay
    ]
  );

  pythonEnv = pythonSet.mkVirtualEnv "logsmith" workspace.deps.default;

  bundledQt = "${pythonEnv}/${python.sitePackages}/PyQt6/Qt6";
in
# Point the interpreter at the Qt that lives inside the PyQt6 wheels, otherwise
# it finds no platform plugin and refuses to start.
pkgs.symlinkJoin {
  name = "logsmith-python-env";
  paths = [ pythonEnv ];
  buildInputs = [ pkgs.makeWrapper ];
  postBuild = ''
    wrapProgram $out/bin/python \
      --set QT_PLUGIN_PATH "${bundledQt}/plugins" \
      --set QML_IMPORT_PATH "${bundledQt}/qml" \
      --prefix LD_LIBRARY_PATH : "${bundledQt}/lib:${lib.makeLibraryPath qtSystemLibs}"
  '';
}
