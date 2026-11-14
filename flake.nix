{
  description = "Logsmith AWS account management utility";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    uv2nix.url = "github:pyproject-nix/uv2nix";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    pyproject-build-systems.url = "github:pyproject-nix/build-system-pkgs";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
    }:
    let
      # The external CLIs logsmith shells out to at runtime. Used by the wrapper
      # of the package, by `home.packages` and by the PATH of the systemd user
      # service, so they are listed once here.
      runtimeTools = pkgs: [
        pkgs.awscli2
        pkgs.google-cloud-sdk
      ];

      homeManagerModules.logsmith = import ./nix/home-manager-module.nix { inherit self runtimeTools; };

      systemIndependentOutputs = {
        inherit homeManagerModules;
        # Aliases for the naming variants home-manager users expect.
        homeManagerModule = homeManagerModules.logsmith;
        homeModules = homeManagerModules;
      };

      perSystemOutputs =
        system:
        let
          pkgs = import nixpkgs { inherit system; };

          pythonEnv = import ./nix/python-env.nix {
            inherit
              pkgs
              uv2nix
              pyproject-nix
              pyproject-build-systems
              ;
            python = pkgs.python313;
            workspaceRoot = ./.;
          };
        in
        {
          packages.default = import ./nix/package.nix {
            inherit pkgs pythonEnv;
            src = ./.;
            runtimeTools = runtimeTools pkgs;
          };
        };
    in
    systemIndependentOutputs // flake-utils.lib.eachDefaultSystem perSystemOutputs;
}
