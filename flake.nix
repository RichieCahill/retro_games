{
  description = "tools for our server";

  nixConfig = {
    extra-substituters = [
      "https://cache.nixos.org/?priority=1&want-mass-query=true"
      "https://cache.tmmworkshop.com/?priority=1&want-mass-query=true"
      "https://nix-community.cachix.org/?priority=10&want-mass-query=true"
    ];
    extra-trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
      "cache.tmmworkshop.com:jHffkpgbmEdstQPoihJPYW9TQe6jnQbWR2LqkNGV3iA="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
      "cache-nix-dot:Od9KN34LXc6Lu7y1ozzV1kIXZa8coClozgth/SYE7dU="
    ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { nixpkgs, flake-utils, ...  }:
  flake-utils.lib.eachDefaultSystem (
    system:
    let 
      pkgs = nixpkgs.legacyPackages.${system};
    in {

      devShells.default = pkgs.mkShell {

        packages = with pkgs; [
          poetry
          python312
        ];
      };
    }
  );
}