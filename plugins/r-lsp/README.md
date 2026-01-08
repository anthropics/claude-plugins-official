# r-lsp

R language server (languageserver) for Claude Code, providing completions, diagnostics, hover info, and symbol navigation for R and R Markdown projects.

## Supported Extensions
`.R`, `.r`, `.Rmd`, `.rmd`

## Installation

### 1. Install R
- **macOS**: `brew install --cask r` or install R from [CRAN](https://cloud.r-project.org)
- **Linux**: install the `r-base` package from your distro's package manager (e.g., `sudo apt install r-base`, `sudo dnf install R`, `sudo pacman -S r`)
- **Windows**: download the R installer from [CRAN](https://cloud.r-project.org/bin/windows/base/) and follow the setup wizard. Install RTools if you plan to compile packages.

Ensure the `R` executable is available on your PATH so Claude Code can start the language server.

### 2. Install the languageserver package
Open an R session (or run via `Rscript`) and install the CRAN package:

```bash
R -q -e "install.packages('languageserver')"
```

For reproducible environments you can add `languageserver` to your `renv`/`pak` manifest or to `DESCRIPTION` under `Imports`.

### 3. Verify the server
```
R -q -e "languageserver::run(check = FALSE)"
```
This should start the server and block until interrupted; exit with `Ctrl+C` once you see it listening. If it fails, reinstall R or the package before enabling the plugin.

## More Information
- [languageserver GitHub](https://github.com/REditorSupport/languageserver)
- [languageserver on CRAN](https://cran.r-project.org/package=languageserver)
- [R Project](https://www.r-project.org/)
