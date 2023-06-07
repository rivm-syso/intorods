@echo off
SETLOCAL EnableDelayedExpansion

set FLAGFILENAME=.
set HASHFILENAME=sha256hashes.txt
set TMPHASHFILENAME=$$$_sha256hashes.txt

FOR /D %%i in (*) do (
    echo Test folder %%i
    set hashfile=%%i\%HASHFILENAME%
    echo Testing for flagfile %%i\%FLAGFILENAME%
    if exist %%i\%FLAGFILENAME% (
	    echo Testing for hashfile !hashfile!
        if not exist !hashfile! (
            echo !hashfile! not found
			set tmphashfile=$$$_ad34rx_%%i
            if exist !tmphashfile! del /f !tmphashfile!
            pushd %%i
            ..\sha256deep -l -r * > ..\!tmphashfile!
            if %errorlevel% equ 0 (move ..\!tmphashfile! %HASHFILENAME%) else (echo Error executing hash256deep.exe)
            popd
        ) else (
            echo Hashfile !hashfile! present
        )
    )
)