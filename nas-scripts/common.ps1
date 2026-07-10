# 公共函数：调用 nas-cli.py，自动初始化虚拟环境并安全读取密码

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ScriptDir ".venv"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$NasCli = Join-Path $ScriptDir "nas-cli.py"

function Ensure-Env {
    if (-not (Test-Path $Python)) {
        Write-Host "首次使用，正在初始化运行环境..." -ForegroundColor Cyan
        & (Join-Path $ScriptDir "setup-env.ps1")
        if (-not (Test-Path $Python)) {
            throw "虚拟环境初始化失败"
        }
    }
}

function Invoke-NasCli {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [string[]]$ExtraArgs = @()
    )

    Ensure-Env

    $SecurePassword = Read-Host "请输入 NAS (coolwing) 密码" -AsSecureString
    $PlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
    )

    try {
        $env:NAS_PASSWORD = $PlainPassword
        & $Python $NasCli $Command @ExtraArgs
    } finally {
        $env:NAS_PASSWORD = $null
        Clear-Variable -Name PlainPassword -ErrorAction SilentlyContinue
    }
}
