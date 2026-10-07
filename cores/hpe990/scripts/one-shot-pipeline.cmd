@echo off
setlocal
for %%I in ("%~dp0..\..\..") do set "PROJECT_ROOT=%%~fI"
if not exist "%PROJECT_ROOT%\pyproject.toml" (
  echo Missing project pyproject.toml 1>&2
  endlocal & exit /b 1
)
if not defined UV_EXE set "UV_EXE=uv"
"%UV_EXE%" --version >nul 2>&1
if errorlevel 1 (
  echo uv is required. Install uv or set UV_EXE to its executable. 1>&2
  endlocal & exit /b 1
)
pushd "%PROJECT_ROOT%" || exit /b 1
"%UV_EXE%" run --locked python -m cores.common.scripts.one_shot_console --uv "%UV_EXE%" %*
set "RESULT=%ERRORLEVEL%"
popd
endlocal & exit /b %RESULT%
