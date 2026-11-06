# Pause / reprise de la campagne D2 N=512 sans perdre le travail deja calcule.
#
# Les captures .npz ne sont ecrites qu'a la FIN de chaque branche : tuer le
# python en cours de branche jetse la chauffe (~2 h) et la capture deja avancee.
# La suspension gelle les threads (CPU = 0) en preservant la memoire du
# processus ; le solveur n'a AUCUNE dependance au temps mural (tout est
# compte en iterations), donc une reprise est numeriquement identique a une
# execution continue.
#
# USAGE (lance depuis n'importe quel repertoire, en PowerShell) :
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/pause_resume_d2.ps1 suspend
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/pause_resume_d2.ps1 status
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/pause_resume_d2.ps1 resume
#
# ATTENTION : l'etat suspendu n'existe que en RAM. Ne redemarrer pas la
# machine et ne pas laisser la veille s'activer, sinon la branche en cours est
# perdue. Si un redemarrage est inevitable, laisser finir la branche en cours
# (le .npz est alors ecrit) puis arreter le launcher avant la branche suivante.
param([Parameter(Mandatory=$true)][ValidateSet('suspend','resume','status')][string]$Action)

$ErrorActionPreference = 'Stop'

$sources = @(
    @{ Label = 'solver python';   Names = 'python.exe','py.exe'; Pattern = 'run_branch_capture_d2\.py' },
    @{ Label = 'launcher bash';   Names = 'bash.exe';            Pattern = 'launch_d2_n512_campaign\.sh' },
    @{ Label = 'tee journal';     Names = 'tee.exe';             Pattern = 'campaign_n512_hold' },
    @{ Label = 'watcher analyse'; Names = 'bash.exe';            Pattern = 'justify_capture_window' }
)

# Le watcher est un bash -c dont la ligne de commande porte le script ; on
# exclut ce processus-ci pour ne pas se suspendre lui-meme.
$self = $PID

function Get-Targets {
    $found = @()
    foreach ($s in $sources) {
        $procs = Get-CimInstance Win32_Process | Where-Object {
            $_.ProcessId -ne $self -and ($s.Names -contains $_.Name) -and
            $_.CommandLine -and $_.CommandLine -match $s.Pattern
        }
        foreach ($p in $procs) {
            if ($p.Name -eq 'powershell.exe') { continue }
            $found += [pscustomobject]@{ Label = $s.Label; Pid = $p.ProcessId; Name = $p.Name }
        }
    }
    return $found
}

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ProcSuspend {
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool CloseHandle(IntPtr h);
    [DllImport("ntdll.dll")] static extern int NtSuspendProcess(IntPtr h);
    [DllImport("ntdll.dll")] static extern int NtResumeProcess(IntPtr h);

    public static string Suspend(int pid) { return Go(pid, true); }
    public static string Resume(int pid)  { return Go(pid, false); }

    static string Go(int pid, bool doSuspend) {
        string last = "OpenProcess a echoue";
        // PROCESS_SUSPEND_RESUME d'abord, ALL_ACCESS en repli si ntdll refuse.
        foreach (uint acc in new uint[] { 0x00000800, 0x001F0FFF }) {
            IntPtr h = OpenProcess(acc, false, pid);
            if (h == IntPtr.Zero) { continue; }
            try {
                int r = doSuspend ? NtSuspendProcess(h) : NtResumeProcess(h);
                if (r == 0) { return "OK"; }
                last = "ntdll status 0x" + r.ToString("X8");
            } finally { CloseHandle(h); }
        }
        return last;
    }
}
'@

$targets = Get-Targets
if ($targets.Count -eq 0) {
    Write-Output "Aucun processus de la campagne D2 N=512 trouve (campagne deja arrete ?)."
    exit 0
}

if ($Action -eq 'status') {
    # NOTE METHODOLOGIQUE : sur ce poste, TotalProcessorTime (Get-Process) et les
    # compteurs de performance (Get-Counter, Win32_PerfFormattedData) sont NON
    # FIABLES : la valeur CPU du solveur est reste figee a 270771 s pendant que
    # le journal progressait de 19 periodes. Le seul indicateur sur est la
    # fraicheur du journal : le runner ecrit UNE ligne par periode simulee, soit
    # ~600 s a N=512. Au-dela de 900 s sans nouvelle ligne => suspendu.
    $root = Split-Path -Parent $PSScriptRoot
    $log = Join-Path $root 'results\09_d2_capture\campaign_n512_hold_c32_20261105_1233_stdout.log'
    $last = $null; $ageMin = $null
    if (Test-Path $log) {
        $line = (Get-Content $log -Tail 1)
        if ($line -match '^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]') {
            $last = [datetime]::ParseExact($matches[1], 'yyyy-MM-dd HH:mm:ss', $null)
            $ageMin = ([datetime]::Now - $last).TotalMinutes
        }
    }
    Write-Output ("{0,-16} {1,7} {2,9} {3,8}  {4}" -f 'LABEL', 'PID', 'CPU s', 'RAM Mo', 'NOTE')
    foreach ($t in $targets) {
        $p = Get-Process -Id $t.Pid -ErrorAction SilentlyContinue
        if (-not $p) { Write-Output ("{0,-16} {1,7}  (termine)" -f $t.Label, $t.Pid); continue }
        Write-Output ("{0,-16} {1,7} {2,9:N0} {3,8:N0}  {4}" -f `
            $t.Label, $t.Pid, $p.TotalProcessorTime.TotalSeconds,
            ($p.WorkingSet64 / 1MB), $(if ($t.Label -like 'solver*') { 'voir journal' } else { '' }))
    }
    if ($null -ne $ageMin) {
        $etat = if ($ageMin -gt 15) { 'SUSPENDU (journal gele)' } else { 'ACTIF' }
        Write-Output ("journal : derniere ligne {0:HH:mm:ss}, {1:N1} min -> {2}" -f $last, $ageMin, $etat)
        Write-Output "(une nouvelle ligne est attendue toutes les ~10 min quand la capture tourne)"
    } else {
        Write-Output "journal introuvable : $log"
    }
    exit 0
}

foreach ($t in $targets) {
    $r = if ($Action -eq 'suspend') { [ProcSuspend]::Suspend($t.Pid) }
         else { [ProcSuspend]::Resume($t.Pid) }
    Write-Output ("{0,-16} PID {1,-7} {2,-8} -> {3}" -f $t.Label, $t.Pid, $Action, $r)
}

if ($Action -eq 'suspend') {
    Write-Output ""
    Write-Output "Reprise : powershell -NoProfile -ExecutionPolicy Bypass -File scripts/pause_resume_d2.ps1 resume"
}
