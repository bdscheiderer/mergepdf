# Build MergePDF.exe on Windows, and the Setup installer when Inno Setup 6
# is installed.
#
# Do this from PowerShell, in any folder. The script moves itself to the
# project folder. Opening the file from File Explorer often opens Notepad,
# so run it from a terminal:
#
#     powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
#
# If you are already in PowerShell:
#
#     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#     .\scripts\build_windows.ps1
#
# Bypass applies only to this window. It does not change the setting for
# the whole PC.
#
# What you get
# ------------
# dist\MergePDF.exe
# installer\MergePDF-1.2-Setup.exe    (only when Inno Setup 6 is installed)
#
# The exe and the installer are not signed. Windows SmartScreen may warn
# the first time they are opened. The README section "First launch on
# Windows" explains that warning.
#
# If the script stops, read the last lines in this window. They name the
# step that failed. Fix that step and run the script again. It is safe to
# run more than once. PyInstaller --clean replaces dist\MergePDF.exe.
#
# This file is written for Windows PowerShell 5.1 (the blue window that
# ships with Windows) and for PowerShell 7. It avoids syntax that only
# PowerShell 7 understands.

#Requires -Version 5.1

# Stop when a PowerShell command fails. This does not apply to the exit
# code of python.exe, PyInstaller, or ISCC.exe. Stop-IfLastCommandFailed
# checks those programs. The Mac build script gets the same check from
# "set -e".
$ErrorActionPreference = "Stop"

# Turn a misspelled variable into an error instead of a silent blank.
Set-StrictMode -Version 3.0

# The script lives in scripts\. Move to the project folder so every
# relative path below (assets, dist, .venv, mergepdf.iss) is correct
# even when PowerShell was sitting somewhere else.
$script:ProjectFolder = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $script:ProjectFolder

Write-Host "Project folder: $script:ProjectFolder"

# A packed MergePDF.exe includes Python, Tk, and the PDF library.
# Anything under this size is an empty or failed build, not the app.
# The real file is usually tens of megabytes. 1 MB is only a floor.
$script:MinimumBuildBytes = 1000000


function Get-ProjectPath {
    # Purpose:
    #     Build a full path inside the project folder.
    #
    # Inputs:
    #     RelativePath - a path such as "dist\MergePDF.exe".
    #
    # Outputs:
    #     The full path as a string.
    #
    # Side effects:
    #     None.
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    return (Join-Path $script:ProjectFolder $RelativePath)
}


function Stop-IfLastCommandFailed {
    # Purpose:
    #     Stop the script when the last program reported a failure.
    #     PowerShell keeps going when python.exe or ISCC.exe returns a
    #     non-zero exit code. This function is the missing check.
    #
    # Inputs:
    #     StepName - words naming the step that just ran, shown in the message.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     Exits the whole script with code 1 when the last program failed
    #     or when no program exit code was recorded.
    #     Call this on the next line after python, pip, PyInstaller, or ISCC.
    param(
        [Parameter(Mandatory = $true)]
        [string]$StepName
    )

    if ($null -eq $LASTEXITCODE) {
        Write-Host ""
        Write-Host "$StepName did not report an exit code."
        exit 1
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "$StepName failed (exit code $LASTEXITCODE)."
        exit 1
    }
}


function Assert-ThisIsWindows {
    # Purpose:
    #     Refuse to build a Windows exe on a Mac or on Linux.
    #     PyInstaller produces MergePDF.exe when it runs on Windows.
    #
    # Inputs:
    #     None. Reads the operating system reported by .NET.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     Exits the script when this computer is not Windows.
    #     Win32NT is the value Windows reports.
    $platform = [System.Environment]::OSVersion.Platform
    if ($platform -ne [System.PlatformID]::Win32NT) {
        Write-Host "This build is for Windows. This computer reports: $platform"
        Write-Host "On a Mac, run:  ./scripts/build_macos.sh"
        exit 1
    }
}


function New-ProjectVirtualEnvironment {
    # Purpose:
    #     Create the .venv folder with the Python launcher from python.org.
    #
    # Inputs:
    #     None.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     Creates .venv in the project folder.
    #     Exits the script when Python cannot be found or venv creation fails.
    #
    # py -3 is preferred. The python.exe under WindowsApps is sometimes a
    # stub that opens the Microsoft Store instead of running Python.
    $pyLauncher = Get-Command -Name "py" -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) {
        Write-Host "Creating .venv with: py -3 -m venv .venv"
        & py -3 -m venv .venv
        Stop-IfLastCommandFailed -StepName "Creating .venv"
        return
    }

    $pythonCommand = Get-Command -Name "python" -ErrorAction SilentlyContinue
    if ($null -ne $pythonCommand) {
        Write-Host "Creating .venv with: python -m venv .venv"
        & python -m venv .venv
        Stop-IfLastCommandFailed -StepName "Creating .venv"
        return
    }

    Write-Host "Python was not found."
    Write-Host "Install it from https://www.python.org/downloads/windows/"
    Write-Host "Check Add python.exe to PATH when the installer offers it."
    Write-Host "Then close this window, open a new PowerShell, and run this script again."
    exit 1
}


function Install-BuildTools {
    # Purpose:
    #     Create a private library folder and install PyInstaller into it.
    #
    # Inputs:
    #     None.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     Creates .venv when Scripts\python.exe is missing.
    #     Deletes an incomplete .venv folder (one with no python.exe) and
    #     creates it again. Source files are not deleted.
    #     Installs requirements-build.txt.
    #     Sets $script:PythonExe to .venv\Scripts\python.exe.
    #     A plain assignment inside a function would stay inside that
    #     function. The script: prefix is what lets later steps use this path.
    $venvFolder = Join-Path $script:ProjectFolder ".venv"
    $scriptsFolder = Join-Path $venvFolder "Scripts"
    $pythonExe = Join-Path $scriptsFolder "python.exe"

    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        if (Test-Path -LiteralPath $venvFolder -PathType Container) {
            Write-Host "The .venv folder has no Scripts\python.exe."
            Write-Host "Removing that incomplete folder and creating it again."
            Remove-Item -LiteralPath $venvFolder -Recurse -Force
        }
        New-ProjectVirtualEnvironment
    }

    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        Write-Host "Creating .venv did not produce Scripts\python.exe."
        Write-Host "Delete the .venv folder and run this script again."
        exit 1
    }

    $script:PythonExe = $pythonExe
    Write-Host "Using $script:PythonExe"
    & $script:PythonExe --version
    Stop-IfLastCommandFailed -StepName "Checking Python"

    # A new venv sometimes ships an older pip. Upgrading it avoids install
    # errors that look like a problem with requirements-build.txt.
    & $script:PythonExe -m pip install --upgrade pip
    Stop-IfLastCommandFailed -StepName "Updating pip"
    & $script:PythonExe -m pip install -r (Get-ProjectPath "requirements-build.txt")
    Stop-IfLastCommandFailed -StepName "Installing requirements-build.txt"
    Test-PythonCanDrawAWindow
}


function Test-PythonCanDrawAWindow {
    # Purpose:
    #     Make sure this Python includes Tcl/Tk, which draws the window.
    #
    # Inputs:
    #     None. Uses $script:PythonExe and scripts\check_tk.py.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     Prints the Tk version when the import works.
    #     Exits with install help when scripts\check_tk.py exits 2,
    #     which means tkinter itself failed to import.
    #     Exits with a different message when the check fails for any
    #     other reason, so that failure is not described as a missing Tk.
    #
    # This runs a .py file on purpose. Do not replace it with python -c.
    # Windows PowerShell 5.1 rewrites quotes in a python -c string before
    # Python starts. The old line was split, and Python saw only:
    #     import tkinter; print(Tk
    # That is a SyntaxError. Tk was never asked to import.
    Write-Host "Checking Tk"
    $checker = Get-ProjectPath "scripts\check_tk.py"
    & $script:PythonExe $checker
    if ($LASTEXITCODE -eq 0) {
        return
    }

    if ($LASTEXITCODE -eq 2) {
        Write-Host ""
        Write-Host "This Python cannot draw a window (tkinter is missing)."
        Write-Host "Install Python from https://www.python.org/downloads/windows/"
        Write-Host "In that installer, leave tcl/tk and IDLE checked."
        Write-Host "If it was turned off, run the installer again, choose Modify, and turn tcl/tk on."
        Write-Host "Then delete the .venv folder and run this script again."
        exit 1
    }

    Write-Host ""
    Write-Host "The Tk check failed (exit code $LASTEXITCODE)."
    Write-Host "The lines above are the Python error. They are not a missing-Tk result."
    Write-Host "Fix that error and run this script again."
    exit 1
}


function Test-IconsNeedRebuild {
    # Purpose:
    #     Decide whether favicon.ico is missing or older than the master PNG.
    #     The exe icon and the installer icon both come from favicon.ico.
    #
    # Inputs:
    #     None. Reads assets\icon.png and assets\favicon.ico.
    #
    # Outputs:
    #     $true when scripts\make_icons.py should run.
    #     $false when the ico file is already current.
    #
    # Side effects:
    #     Prints a one-line reason when a rebuild is required because the
    #     ico is missing or older than the PNG.
    #     Does not write icon files. This function must not use Write-Output.
    #     In PowerShell, Write-Output becomes part of the return value.
    $png = Get-ProjectPath "assets\icon.png"
    $ico = Get-ProjectPath "assets\favicon.ico"

    if (-not (Test-Path -LiteralPath $png -PathType Leaf)) {
        return $true
    }
    if (-not (Test-Path -LiteralPath $ico -PathType Leaf)) {
        Write-Host "assets\favicon.ico is missing. It will be rebuilt from assets\icon.png."
        return $true
    }

    $pngTime = (Get-Item -LiteralPath $png).LastWriteTimeUtc
    $icoTime = (Get-Item -LiteralPath $ico).LastWriteTimeUtc
    if ($pngTime -gt $icoTime) {
        Write-Host "assets\icon.png is newer than assets\favicon.ico. The icon will be rebuilt."
        return $true
    }

    return $false
}


function Update-IconsIfNeeded {
    # Purpose:
    #     Rebuild favicon.ico from the red m PNG when the ico is missing
    #     or older than the PNG.
    #
    # Inputs:
    #     None.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     May run scripts\make_icons.py, which rewrites assets\favicon.ico
    #     and assets\icon.icns. The icns file is for the Mac app. The Mac
    #     build script replaces it with Apple's iconutil version later.
    #     Exits the script when the icon script fails.
    $rebuild = Test-IconsNeedRebuild
    if ($rebuild -eq $true) {
        Write-Host "Refreshing icons from assets\icon.png"
        & $script:PythonExe (Get-ProjectPath "scripts\make_icons.py")
        Stop-IfLastCommandFailed -StepName "Rebuilding icons"
        return
    }

    Write-Host "assets\favicon.ico is already up to date. Skipping scripts\make_icons.py."
    Write-Host "Delete assets\favicon.ico and run this script again to force a rebuild."
}


function Assert-IconFilesExist {
    # Purpose:
    #     Stop before PyInstaller if an icon file the spec packs is missing.
    #
    # Inputs:
    #     None.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     Exits the script when assets\icon.png or assets\favicon.ico is missing.
    $relativePaths = @(
        "assets\icon.png",
        "assets\favicon.ico"
    )
    foreach ($relativePath in $relativePaths) {
        $fullPath = Get-ProjectPath $relativePath
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            Write-Host "Missing $relativePath"
            Write-Host "assets\icon.png is the master picture."
            Write-Host "assets\favicon.ico is the exe icon. scripts\make_icons.py creates it from the PNG."
            exit 1
        }
    }
}


function Assert-FileIsLargeEnough {
    # Purpose:
    #     Confirm a build output exists and is large enough to be the real app.
    #
    # Inputs:
    #     Path - full path of the file to check.
    #     Label - short name printed in messages, such as "dist\MergePDF.exe".
    #     MinimumBytes - smallest acceptable size. Smaller means the build
    #         did not pack Python into the file.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     Prints the size in megabytes.
    #     Exits the script when the file is missing or too small.
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [long]$MinimumBytes
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Write-Host "$Label was not created."
        Write-Host $Path
        exit 1
    }

    $size = (Get-Item -LiteralPath $Path).Length
    if ($size -lt $MinimumBytes) {
        Write-Host "$Label is only $size bytes. A real build is much larger."
        Write-Host "Expected at least $MinimumBytes bytes."
        Write-Host $Path
        exit 1
    }

    $megabytes = [math]::Round($size / 1MB, 1)
    Write-Host "$Label ($megabytes MB)"
    Write-Host $Path
}


function Build-WindowsExe {
    # Purpose:
    #     Run PyInstaller and require dist\MergePDF.exe.
    #
    # Inputs:
    #     None.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     Deletes and recreates the PyInstaller work under build\ and dist\.
    #     --clean drops leftovers from an older icon so Windows cannot keep
    #     showing a previous picture.
    #     --noconfirm replaces an existing dist\MergePDF.exe.
    #     Exits the script when PyInstaller fails or the exe is missing.
    Assert-IconFilesExist
    Write-Host "Running PyInstaller"
    Write-Host "Close MergePDF first if it is already open. Windows will not replace an exe that is running."
    & $script:PythonExe -m PyInstaller --noconfirm --clean "MergePDF-windows.spec"
    Stop-IfLastCommandFailed -StepName "PyInstaller"

    $exePath = Get-ProjectPath "dist\MergePDF.exe"
    Assert-FileIsLargeEnough -Path $exePath -Label "dist\MergePDF.exe" -MinimumBytes $script:MinimumBuildBytes
}


function Find-InnoCompiler {
    # Purpose:
    #     Find ISCC.exe, the Inno Setup command-line compiler.
    #
    # Inputs:
    #     None. Looks in Program Files, Program Files (x86), then on PATH.
    #
    # Outputs:
    #     The full path of ISCC.exe when it is found.
    #     $null when Inno Setup 6 is not installed in those places.
    #
    # Side effects:
    #     None.
    #     This function must not use Write-Output. In PowerShell, anything
    #     written that way becomes part of the return value, and the caller
    #     would no longer receive a plain path.
    #
    # Inno Setup 6's own installer is 32-bit, so ISCC.exe usually lands in
    # "Program Files (x86)" even on a 64-bit PC. That folder is checked first.
    $candidates = @()

    $programFilesX86 = ${env:ProgramFiles(x86)}
    if ($programFilesX86) {
        $candidates += (Join-Path $programFilesX86 "Inno Setup 6\ISCC.exe")
    }
    if ($env:ProgramFiles) {
        $candidates += (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
    }

    # @() keeps a single path as a list. Without it, PowerShell can turn a
    # one-item list into plain text, and this loop would then walk each letter.
    foreach ($candidate in @($candidates)) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }

    $onPath = Get-Command -Name "ISCC.exe" -ErrorAction SilentlyContinue
    if ($null -ne $onPath) {
        return $onPath.Source
    }

    return $null
}


function Assert-InstallerInputs {
    # Purpose:
    #     Check the files mergepdf.iss names, before Inno Setup runs.
    #
    # Inputs:
    #     None.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     Exits the script when one of those files is missing.
    #     mergepdf.iss copies dist\MergePDF.exe, shows LICENSE.txt, and uses
    #     assets\favicon.ico as the installer icon.
    $relativePaths = @(
        "mergepdf.iss",
        "LICENSE.txt",
        "assets\favicon.ico",
        "dist\MergePDF.exe"
    )
    foreach ($relativePath in $relativePaths) {
        $fullPath = Get-ProjectPath $relativePath
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            Write-Host "Cannot build the installer. Missing: $relativePath"
            exit 1
        }
    }
}


function Show-MissingInnoSteps {
    # Purpose:
    #     Tell a person how to install Inno Setup and produce the Setup file.
    #
    # Inputs:
    #     None.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     Prints the next steps. Does not exit. dist\MergePDF.exe is already
    #     built, so a missing compiler is not a failed program build.
    Write-Host ""
    Write-Host "dist\MergePDF.exe is ready. The installer was not built."
    Write-Host "Inno Setup 6 (ISCC.exe) was not found."
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Install Inno Setup 6 from https://jrsoftware.org/isdl.php"
    Write-Host "     The default folders are fine. This script looks in:"
    Write-Host "       C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    Write-Host "       C:\Program Files\Inno Setup 6\ISCC.exe"
    Write-Host "  2. Open a new PowerShell in this project folder and run:"
    Write-Host "       .\scripts\build_windows.ps1"
    Write-Host "     Or compile the installer yourself, from this folder:"
    Write-Host '       & "C:\Program Files\Inno Setup 6\ISCC.exe" mergepdf.iss'
    Write-Host "     If Inno is in the (x86) folder, use that path instead."
    Write-Host "  3. The installer is written to:"
    Write-Host "       installer\MergePDF-1.2-Setup.exe"
    Write-Host ""
    Write-Host "You can run dist\MergePDF.exe on this PC without the installer."
    Write-Host "Ship installer\MergePDF-1.2-Setup.exe when you want to give MergePDF to someone else."
    Write-Host "Windows SmartScreen may warn the first time. Choose More info, then Run anyway."
    Write-Host "The README section `"First launch on Windows`" describes that screen."
}


function Build-InstallerIfInnoIsInstalled {
    # Purpose:
    #     Compile mergepdf.iss when Inno Setup 6 is installed.
    #
    # Inputs:
    #     None.
    #
    # Outputs:
    #     None.
    #
    # Side effects:
    #     When ISCC.exe is found, removes any previous
    #     installer\MergePDF-1.2-Setup.exe and compiles a new one.
    #     The old file is removed first so a failed compile cannot leave
    #     last week's installer looking like a success.
    #     The output name comes from OutputDir and OutputBaseFilename in
    #     mergepdf.iss. Those lines say installer\MergePDF-1.2-Setup.exe.
    #     When ISCC.exe is missing, prints next steps and leaves the exe in place.
    #     Exits the script when Inno Setup is found but the compile fails.
    $compiler = Find-InnoCompiler
    if ($null -eq $compiler) {
        Show-MissingInnoSteps
        return
    }

    Write-Host "Using Inno Setup: $compiler"
    Assert-InstallerInputs

    $installer = Get-ProjectPath "installer\MergePDF-1.2-Setup.exe"
    if (Test-Path -LiteralPath $installer -PathType Leaf) {
        Write-Host "Removing the previous installer so a failed compile cannot leave an old file in place."
        Remove-Item -LiteralPath $installer -Force
    }

    $issFile = Get-ProjectPath "mergepdf.iss"
    & $compiler $issFile
    Stop-IfLastCommandFailed -StepName "Inno Setup"

    Assert-FileIsLargeEnough -Path $installer -Label "installer\MergePDF-1.2-Setup.exe" -MinimumBytes $script:MinimumBuildBytes

    Write-Host ""
    Write-Host "Built:"
    Write-Host "    dist\MergePDF.exe"
    Write-Host "    installer\MergePDF-1.2-Setup.exe"
    Write-Host ""
    Write-Host "The installer is not signed. The first time it is opened, Windows"
    Write-Host "SmartScreen may warn. Choose More info, then Run anyway."
    Write-Host "Some Windows versions say Open anyway. The README section"
    Write-Host "First launch on Windows describes that screen."
}


# The steps run in this order. Each function stops the script when its
# own step fails. A missing Inno Setup install does not undo the exe.
Assert-ThisIsWindows
Install-BuildTools
Update-IconsIfNeeded
Build-WindowsExe
Build-InstallerIfInnoIsInstalled
