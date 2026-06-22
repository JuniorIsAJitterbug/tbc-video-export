{
  config,
  decodeToolSets,
  defaultSets,
  lib,
  pkgs,
  pyEnvs,
  pyWorkspace,
  toolSettings,
  ...
}:
let
  mkEditableSet =
    {
      pySet,
    }:
    pySet.overrideScope (
      lib.composeManyExtensions [
        (pyWorkspace.mkEditablePyprojectOverlay { root = "$REPO_ROOT"; })
        (final: prev: {
          tbc-video-export = prev.tbc-video-export.overrideAttrs (prevAttrs: {
            # filter to prevent rebuilds
            src = lib.fileset.toSource {
              root = prevAttrs.src;
              fileset = lib.fileset.unions [
                (prevAttrs.src + "/pyproject.toml")
                (prevAttrs.src + "/README.md")
                (prevAttrs.src + "/src/tbc_video_export/__init__.py")
              ];
            };

            # fix for hatchling when using editable venv
            nativeBuildInputs =
              (prevAttrs.nativeBuildInputs or [ ]) ++ final.resolveBuildSystem { editables = [ ]; };
          });
        })
      ]
    );

  mkDevShell =
    {
      pyEnv,
      toolSet,
    }:
    shellName:
    let
      set = mkEditableSet { inherit (pyEnv) pySet; };
      venv = set.mkVirtualEnv "tbc-video-export-${shellName}-env" pyWorkspace.deps.all;

      vscode = {
        settingsFile = (pkgs.formats.json { }).generate "vscode-settings.json" {
          # keep-sorted start block=yes

          "[markdown]" = {
            "editor.defaultFormatter" = "rvben.rumdl";
          };
          "[nix]" = {
            "editor.defaultFormatter" = "jnoortheen.nix-ide";
          };
          "[python]" = {
            "editor.defaultFormatter" = "charliermarsh.ruff";
            "editor.codeActionsOnSave" = {
              "source.organizeImports" = "explicit";
            };
          };
          "[toml]" = {
            "editor.defaultFormatter" = "tombi-toml.tombi";
          };
          "[yaml]" = {
            "editor.defaultFormatter" = "bluebrown.yamlfmt";
          };
          "direnv.path.executable" = lib.getExe pkgs.direnv;
          "editor.formatOnSave" = true;
          "nix.enableLanguageServer" = true;
          "nix.serverPath" = lib.getExe pkgs.nixd;
          "nix.serverSettings" = {
            "nixd" = {
              "formatting" = {
                command = [ (lib.getExe pkgs.nixfmt-rs) ];
              };
            };
          };
          "pyrefly.lspPath" = lib.getExe pkgs.pyrefly;
          "python.defaultInterpreterPath" = "\${env:UV_PYTHON}";
          "ruff.configurationPreference" = "filesystemFirst";
          "ruff.path" = [ (lib.getExe pkgs.ruff) ];
          "rumdl.fixOnSave" = true;
          "rumdl.server.path" = lib.getExe pkgs.rumdl;
          "tombi.args" = [ "lsp" ];
          "tombi.path" = lib.getExe pkgs.tombi;
          "typos.path" = lib.getExe pkgs.typos-lsp;
          "yamlfmt.args" = [
            "-conf"
            toolSettings.yamlfmt
          ];
          "zizmor.executablePath" = lib.getExe pkgs.zizmor;
          # keep-sorted end
        };

        extensionsFile = (pkgs.formats.json { }).generate "vscode-settings.json" {
          recommendations = [
            # keep-sorted start
            "bluebrown.yamlfmt"
            "charliermarsh.ruff"
            "jnoortheen.nix-ide"
            "meta.pyrefly"
            "mkhl.direnv"
            "ms-python.python"
            "rvben.rumdl"
            "tekumara.typos-vscode"
            "tombi-toml.tombi"
            "zizmorcore.zizmor-vscode"
            # keep-sorted end
          ];
        };
      };
    in
    pkgs.mkShell {
      packages = [
        venv
        pyEnv.pkgSet.ffmpeg
        toolSet.package

        pkgs.mediainfo
        pkgs.uv
      ]
      # add pkgs used by git-hooks
      ++ config.pre-commit.settings.enabledPackages;

      env = {
        UV_NO_SYNC = "1";
        UV_PROJECT_ENVIRONMENT = venv;
        UV_PYTHON = "${venv}/bin/python";
        UV_PYTHON_DOWNLOADS = "never";
      };

      shellHook = ''
        # used by pre-commit hooks and nix
        export GITHUB_TOKEN="''${GITHUB_TOKEN:-$(gh auth token 2>/dev/null || true)}"
        [ -z "$GITHUB_TOKEN" ] && echo "!! GITHUB_TOKEN is unset"

        export NIX_CONFIG="${''
          accept-flake-config = true                  # required for extra-substituters
          access-tokens = github.com="$GITHUB_TOKEN"  # prevent rate-limit
        ''}"

        # pyproject
        export REPO_ROOT=$(git rev-parse --show-toplevel)
        unset PYTHONPATH

        [ ! -d "$REPO_ROOT/.vscode" ] && mkdir "$REPO_ROOT/.vscode"
        ln -f -s "${vscode.settingsFile}" "$REPO_ROOT/.vscode/settings.json"
        ln -f -s "${vscode.extensionsFile}" "$REPO_ROOT/.vscode/extensions.json"

        ${config.pre-commit.shellHook}
      '';
    };

  default = mkDevShell { inherit (defaultSets) pyEnv toolSet; } "dev";
in
{
  devShells = {
    inherit default;
  }
  // lib.listToAttrs (
    lib.lists.crossLists
      (
        pyEnv: toolSet:
        let
          name = "devShell-${toolSet.name}-${pyEnv.name}";
        in
        {
          inherit name;
          value = mkDevShell { inherit pyEnv toolSet; } name;
        }
      )
      [
        pyEnvs
        decodeToolSets
      ]
  );
}
