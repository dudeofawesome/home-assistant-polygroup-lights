{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

{
  # https://devenv.sh/packages/
  packages = with pkgs; [
    esphome
    platformio
    ruff
  ];

  # https://devenv.sh/languages/
  languages.python = {
    enable = true;
    version = "3.14";

    venv.enable = true;
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  # https://devenv.sh/services/
  # services.postgres.enable = true;
}
