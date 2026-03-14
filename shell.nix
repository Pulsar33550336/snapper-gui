# shell.nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: [
      ps.dbus-python
      ps.pygobject3
      ps.pyside6
    ]))
  ];
}
