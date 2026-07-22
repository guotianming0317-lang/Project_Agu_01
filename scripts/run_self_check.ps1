$ErrorActionPreference = "Stop"

function Get-ProjectPythonCommand {
    $codexPython = "C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $codexPython) {
        return @{
            Exe = $codexPython
            Args = @()
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return @{
            Exe = $pythonCommand.Source
            Args = @()
        }
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        return @{
            Exe = $pyCommand.Source
            Args = @("-3")
        }
    }

    throw "No usable Python interpreter was found. Install Python or add python.exe to PATH."
}

$pythonCommand = Get-ProjectPythonCommand
& $pythonCommand.Exe @($pythonCommand.Args) -m app.main self-check
