{
  inputs = {
    nixpkgs.url = "github:cachix/devenv-nixpkgs/rolling";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";
    nixpkgs-python = {
      url = "github:cachix/nixpkgs-python";
      inputs = {
        nixpkgs.follows = "nixpkgs";
      };
    };
  };

  nixConfig = {
    extra-trusted-public-keys = "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs =
    {
      self,
      nixpkgs,
      devenv,
      systems,
      ...
    }@inputs:
    let
      forEachSystem = nixpkgs.lib.genAttrs (import systems);
    in
    {
      devShells = forEachSystem (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = devenv.lib.mkShell {
            inherit inputs pkgs;
            modules = [
              {
                # https://devenv.sh/reference/options/
                packages = with pkgs; [
                  pyright # python lsp
                  ruff # fast linter

                  # for pick file support
                  python313Packages.tkinter
                  python313Packages.numpy
                ];

                # https://devenv.sh/reference/options/
                languages.python = {
                  enable = true;
                  version = "3.13";
                  uv = {
                    enable = true;
                    sync.enable = true;
                  };
                };

                scripts.init-project.exec = ''
                  
                  ${pkgs.uv}/bin/uv init
                  ${pkgs.uv}/bin/uv sync
                  ${pkgs.uv}/bin/uv add --dev -r dev-requirements.txt
                '';

                enterShell = "source .devenv/state/venv/bin/activate";

                # env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
                #   pkgs.stdenv.cc.cc
                #   pkgs.zlib
                #   pkgs.libGL
                #   pkgs.glib
                # ];
              }
            ];
          };
        }
      );
    };
}
