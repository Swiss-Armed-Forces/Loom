# The VM tests, as a Python package the test driver imports.
#
# Each nixos/tests/*.nix installs this through `extraPythonPackages` and its testScript
# is then two lines: an import and the call. What that replaced was `builtins.readFile`,
# which concatenated every script the driver ran into one namespace -- so two files could
# not both `import json` without the driver's own ruff rejecting the pair, a reference
# across files was a pylint `used-before-assignment`, and nothing could be shared between
# tests at all. See loom_tests/driver.py.
#
# Built from *inside* the `extraPythonPackages` callback rather than from the repository's
# `pkgs`, which is the one thing about this file that is not cosmetic: the argument is the
# driver's own Python package set, so the package is built for the interpreter that will
# import it by construction rather than by assuming the two match.
#
# poetry-core, like every other Python project here -- the lockfile beside pyproject.toml
# is what keeps `poetry lock` honest about what the devenv's virtualenv gets, while the
# dependencies Nix resolves come from nixpkgs. The suite under `scripts/tests/` covers the
# pure helpers -- the screen decoder and the tmux parser -- and runs in `checkPhase`, so a
# mistake in either fails this build rather than a VM boot ten minutes later.
{ pythonPackages }:
pythonPackages.buildPythonPackage {
  pname = "loom-tests";
  version = "0.1.0";
  src = ./scripts;
  pyproject = true;

  build-system = [ pythonPackages.poetry-core ];
  nativeCheckInputs = [ pythonPackages.pytest ];

  checkPhase = ''
    runHook preCheck
    # Appended rather than assigned, so the paths the python setup hook exported for
    # this package survive; `tests` as well, because the suite imports its fake machine
    # by module name the way pytest's rootdir insertion would.
    PYTHONPATH=$PWD:$PWD/tests''${PYTHONPATH:+:$PYTHONPATH} pytest tests -q
    runHook postCheck
  '';

  # Nothing in this closure imports the package -- the test driver does -- so this is
  # the only thing standing between a module that does not import and a VM that boots
  # for ten minutes before saying so.
  pythonImportsCheck = [ "loom_tests" ];
}
