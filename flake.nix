{
  description = "Live Discord REST API and Gateway latency monitor";

  inputs = {
    nixpkgs.url     = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs      = import nixpkgs { inherit system; };
        python    = pkgs.python3;

        discord-ping = python.pkgs.buildPythonApplication {
          pname   = "discord-ping";
          version = "1.0.0";
          format  = "pyproject";
          src     = ./.;

          build-system = with python.pkgs; [ setuptools ];

          propagatedBuildInputs = with python.pkgs; [ aiohttp ];

          meta = with pkgs.lib; {
            description = "Live Discord REST API and Gateway latency monitor";
            homepage    = "https://github.com/drlove2002/discord-ping";
            license     = licenses.mit;
            mainProgram = "discord-ping";
          };
        };
      in
      {
        packages.default = discord-ping;

        apps.default = {
          type    = "app";
          program = "${discord-ping}/bin/discord-ping";
        };
      }
    );
}
