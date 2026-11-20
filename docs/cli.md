<!-- The textkit command line (textkit/__main__.py), plan task T2.6. -->
# Command line

```bash
python3 -m textkit <function> "<text>"
python3 -m textkit --help
python3 -m textkit --version
```

`python3 -m textkit` runs one textkit function on one text argument and prints the result.
`--help` lists every available function with the first line of its docstring;
`python3 -m textkit <function> --help` shows the help for one function.

## Version

`python3 -m textkit --version` prints `textkit <version>` (today `textkit 0.1.0`) to stdout
and exits 0 (plan task T2.7). The version string lives only in `textkit/__init__.py` as
`__version__`; `__main__.py` reads `textkit.__version__` (argparse's `action="version"`), so
a release changes that one line.

## Which functions are commands

The commands are discovered at run time (`_commands` in `textkit/__main__.py`), never listed
by hand. A function is a command when:

- it is a **public function** under the phase 1 definition: a top-level function whose name
  does not start with `_`, in a `textkit` module whose name does not start with `_`
  (modules come from `pkgutil.iter_modules(textkit.__path__)`);
- its `__module__` is the module being scanned, so a function imported from elsewhere is
  not listed twice;
- it has **exactly one parameter without a default** (`*args` and `**kwargs` do not count).
  The text goes to that parameter; every parameter with a default keeps its default.

So `slugify(text)` is a command and `truncate(text, width, suffix="...")` is not: it needs
two arguments. A new function that fits becomes a command with no change to the CLI.
`tests/test_cli.py` computes the same set independently and checks that `--help` lists
exactly it, then runs every command once in a subprocess.

## Arguments

Exactly one text argument: quote it so the shell passes it as one word. A text that starts
with `-` would be read as an option; put `--` before it:

```bash
python3 -m textkit squeeze -- "-x   y"     # prints "-x y"
```

## Output

The result is printed to stdout, followed by a newline:

| Result type | Printed as |
|-------------|------------|
| `str` | as is (`hello-world`) |
| `bool`, `int` | with `print()` (`True`, `3`) |
| `dict`, `list` | `json.dumps(result, ensure_ascii=False, sort_keys=True)` (`{"a": 1, "ñ": 1}`) |

Any other type is printed with `print()` as well.

## Exit status

| Status | When | Where the message goes |
|--------|------|------------------------|
| 0 | success, and after `--help` or `--version` | result or help on stdout |
| 1 | the function raised `ValueError` (none of the current commands can) | `textkit: error: <message>` on stderr |
| 2 | no arguments, an unknown function, a function that is not a command, or a wrong argument count | usage and error on stderr |

With no arguments the usage goes to stderr and the status is 2. On Python 3.9 this needs
`add_subparsers(dest="command", required=True)`: without `dest`, argparse fails with a
`TypeError` while building the "required" error message.

## Entry point

`_main(argv: Optional[List[str]] = None) -> int` parses `argv` (default `sys.argv[1:]`) and
returns the exit status instead of exiting, so tests can call it in-process. The module calls
it only under `if __name__ == "__main__":`, so importing `textkit.__main__` has no side
effects. `__main__.py` contains no public functions (its helpers all start with `_`), so it
needs no README row; the CHANGELOG has one line for the command line as a whole.
