@echo off
setlocal
for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"
if not exist "%PROJECT_ROOT%\pyproject.toml" (
  echo Missing project pyproject.toml 1>&2
  endlocal & exit /b 1
)
if defined UV_EXE goto uv_ready
for %%U in (uv.exe) do set "UV_EXE=%%~$PATH:U"
if defined UV_EXE goto uv_ready
if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV_EXE=%USERPROFILE%\.local\bin\uv.exe"
if defined UV_EXE goto uv_ready
if exist "%PROJECT_ROOT%\..\pk_system\uv.exe" set "UV_EXE=%PROJECT_ROOT%\..\pk_system\uv.exe"
if not defined UV_EXE set "UV_EXE=uv"
:uv_ready
"%UV_EXE%" --version >nul 2>&1
if errorlevel 1 (
  echo uv is required. Install uv or set UV_EXE to its executable. 1>&2
  endlocal & exit /b 1
)
pushd "%PROJECT_ROOT%" || exit /b 1
"%UV_EXE%" run --locked python -m cores.hpe990.scripts.share_tc_review --open-browser %*
set "RESULT=%ERRORLEVEL%"
popd
endlocal & exit /b %RESULT%
