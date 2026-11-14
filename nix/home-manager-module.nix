# home-manager module: installs logsmith, optionally writes its configuration
# files and autostarts it as a systemd user service.
#
# System independent on purpose - `pkgs` is the one of the importing
# home-manager configuration, `self` is only used to look up the default
# package for that system.
{ self, runtimeTools }:
{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.programs.logsmith;

  tools = runtimeTools pkgs;

  yamlType = (pkgs.formats.yaml { }).type;

  # Written as json, which is a subset of yaml, so no converter has to be built
  # just to render a config file.
  toYamlFile = (pkgs.formats.json { }).generate;

  # PATH for the systemd service: the user supplied directories first, then the
  # store paths of the packages logsmith and the post login scripts call.
  servicePath = lib.concatStringsSep ":" (
    cfg.extraPaths ++ [ (lib.makeBinPath (tools ++ cfg.extraPackages)) ]
  );

  # `~/.logsmith/<fileName>` is only managed by nix when the option is set.
  # An empty attribute set means "leave the file alone", so that logsmith itself
  # can keep writing it.
  declarativeFile =
    fileName: value:
    lib.mkIf (value != { }) {
      ".logsmith/${fileName}".source = toYamlFile "logsmith-${fileName}" value;
    };
in
{
  options.programs.logsmith = {
    enable = lib.mkEnableOption "logsmith aws login helper";

    package = lib.mkOption {
      type = lib.types.package;
      default = self.packages.${pkgs.system}.default;
      defaultText = lib.literalExpression "logsmith.packages.\${pkgs.system}.default";
      description = "The logsmith package to use.";
    };

    autostart = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Start logsmith as a systemd user service with the graphical session.";
    };

    extraPackages = lib.mkOption {
      type = lib.types.listOf lib.types.package;
      default = [ ];
      example = lib.literalExpression "[ pkgs.kubectl pkgs.kubelogin ]";
      description = ''
        Additional packages that are installed and put on the PATH of the
        service, for tools used by the post login scripts of a profile group.
      '';
    };

    extraPaths = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [ ];
      example = lib.literalExpression ''
        [
          "''${config.home.homeDirectory}/.asdf/shims"
          "''${config.home.homeDirectory}/.krew/bin"
        ]
      '';
      description = ''
        Additional directories that are prepended to the PATH of the service.

        The service is started by systemd and not by an interactive shell, so
        directories that are added in `~/.zshrc` or `~/.bashrc` are neither
        visible to logsmith nor to the post login scripts.
      '';
    };

    settings = lib.mkOption {
      type = lib.types.attrsOf yamlType;
      default = { };
      example = lib.literalExpression ''
        {
          default_access_key = "access-key";
          default_sso_session = "sso";
          mfa_shell_command = "pass otp aws";
        }
      '';
      description = ''
        Declarative content of `~/.logsmith/config.yaml`, written as a nix
        attribute set (not as a yaml string).

        When set, the file becomes a read-only symlink into the nix store and
        logsmith's "Edit Config" dialog can no longer write to it.
      '';
    };

    accounts = lib.mkOption {
      type = lib.types.attrsOf yamlType;
      default = { };
      example = lib.literalExpression ''
        {
          my-team = {
            color = "#388E3C";
            region = "eu-central-1";
            profiles = [
              {
                profile = "developer";
                account = "123456789012";
                role = "developer";
              }
            ];
          };
        }
      '';
      description = ''
        Declarative content of `~/.logsmith/accounts.yaml` (the profile groups),
        written as a nix attribute set (not as a yaml string).

        When set, the file becomes a read-only symlink into the nix store and
        logsmith's config dialog can no longer write to it.
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [ cfg.package ] ++ tools ++ cfg.extraPackages;

    home.file = lib.mkMerge [
      (declarativeFile "config.yaml" cfg.settings)
      (declarativeFile "accounts.yaml" cfg.accounts)
    ];

    systemd.user.services.logsmith = lib.mkIf cfg.autostart {
      Unit = {
        Description = "logsmith aws login helper";
        # Needs both a tray to dock into and network access to reach AWS.
        After = [
          "graphical-session.target"
          "network-online.target"
        ];
        Wants = [ "network-online.target" ];
        PartOf = [ "graphical-session.target" ];
      };
      Service = {
        Type = "simple";
        # Started via a shell to extend the PATH of the systemd user manager
        # instead of replacing it. logsmith collects its environment from a
        # non-interactive login shell, which only inherits this PATH, so
        # everything the post login scripts need has to be on it.
        # `$$PATH` escapes the `$` for systemd, the shell sees `$PATH`.
        ExecStart = "${pkgs.runtimeShell} -c 'PATH=${servicePath}:$$PATH exec ${cfg.package}/bin/logsmith'";
        Restart = "on-failure";
        RestartSec = "5s";
      };
      Install.WantedBy = [ "graphical-session.target" ];
    };
  };
}
