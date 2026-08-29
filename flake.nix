{
  description = "logsmith - AWS credential management tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Python 3.13 with runtime dependencies resolved via nixpkgs.
        # Using nixpkgs PyQt6 (not the PyPI wheel) means Qt is properly linked
        # in the Nix store - no LD_LIBRARY_PATH workaround needed for the package.
        python = pkgs.python313.withPackages (ps: with ps; [
          boto3
          pyqt6
          ruamel-yaml
        ]);

        logsmith = pkgs.stdenv.mkDerivation {
          pname = "logsmith";
          version = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).project.version;

          src = self;

          nativeBuildInputs = [ pkgs.makeWrapper ];
          buildInputs = [ python ];

          dontBuild = true;

          installPhase = ''
            runHook preInstall

            src_dir=$out/share/logsmith
            mkdir -p $src_dir $out/bin

            # Only the app/ package is needed at runtime; skip tests, docs, dev tooling.
            cp -r app $src_dir/

            # Python adds app/run.py's directory (app/) to sys.path[0] automatically,
            # covering bare imports (arguments, cli, gui, ...).
            # PYTHONPATH=$src_dir covers package-style imports (from app.X import Y).
            # awscli2 is appended to PATH because SSO login shells out to `aws sso login`.
            makeWrapper ${python}/bin/python $out/bin/logsmith \
              --add-flags "$src_dir/app/run.py" \
              --set PYTHONPATH "$src_dir" \
              --suffix PATH : "${pkgs.awscli2}/bin"

            runHook postInstall
          '';

          meta = with pkgs.lib; {
            description = "Trayicon to assume your favorite AWS roles and manage GCP config";
            homepage = "https://github.com/otto-de/logsmith";
            license = licenses.asl20;
            mainProgram = "logsmith";
            platforms = platforms.linux;
          };
        };

        # Libraries required by PyQt6 wheels from PyPI (bundled Qt needs these at runtime).
        # Only used by the devShell (uv/PyPI workflow).
        qtRuntimeLibs = with pkgs; [
          stdenv.cc.cc.lib
          zlib
          libGL
          libxkbcommon
          glib
          fontconfig
          freetype
          dbus
          xorg.libxcb
          xorg.libX11
          xorg.libXext
          xorg.libXrender
          xorg.libXi
          xorg.libXrandr
          xorg.libXfixes
          xorg.xcbutil
          xorg.xcbutilimage
          xorg.xcbutilkeysyms
          xorg.xcbutilrenderutil
          xorg.xcbutilwm
          xorg.xcbutilcursor
          wayland
        ];
      in
      {
        packages.default = logsmith;

        apps.default = {
          type = "app";
          program = "${logsmith}/bin/logsmith";
        };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python313
            uv
          ] ++ qtRuntimeLibs;

          shellHook = ''
            export PYTHONPATH="$PWD''${PYTHONPATH:+:$PYTHONPATH}"
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath qtRuntimeLibs}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
          '';
        };
      }
    );
}
