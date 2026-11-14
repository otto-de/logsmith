# The `logsmith` executable: the app sources plus a wrapper that runs them with
# the prebuilt python environment and the runtime CLIs on the PATH.
{
  pkgs,
  pythonEnv,
  runtimeTools,
  src,
}:
let
  inherit (pkgs) lib;

  # Single source of truth for the version is app/version.py.
  version = lib.head (
    builtins.match ''.*version[[:space:]]*=[[:space:]]*"([^"]+)".*'' (
      builtins.readFile "${src}/app/version.py"
    )
  );
in
pkgs.stdenv.mkDerivation {
  pname = "logsmith";
  inherit version src;

  nativeBuildInputs = [ pkgs.makeWrapper ];
  buildInputs = [ pythonEnv ];

  installPhase = ''
    mkdir -p $out/bin $out/share/logsmith
    cp -r app $out/share/logsmith/
    makeWrapper ${pythonEnv}/bin/python $out/bin/logsmith \
      --add-flags $out/share/logsmith/app/run.py \
      --prefix PYTHONPATH : $out/share/logsmith \
      --prefix PATH : ${lib.makeBinPath runtimeTools}
  '';
}
