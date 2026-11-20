# Start here (Windows PowerShell)

1. Extract this package to a folder such as `C:\Users\<you>\financial-complaint-analytics`.
2. Open Windows PowerShell in that extracted folder.
3. Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\publish_project.ps1 -Visibility public
```

The script checks Git and GitHub CLI, checks `gh auth status`, searches Desktop/Documents/Downloads/OneDrive for a PBIX whose name contains `Complaint` or `Analytics`, and copies the newest match into `powerbi/` locally. It creates and pushes `https://github.com/<your-login>/financial-complaint-analytics`.

If Git or GitHub CLI is not installed:

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
```

Close and reopen PowerShell, then authenticate once:

```powershell
gh auth login
```

Run the publishing script again.

**Important:** the script defaults to a public repository so the internship reviewer can open the URL. It excludes the raw CSV, cleaned CSV, and PBIX. Keep the PBIX for upload separately unless you have confirmed that publishing its embedded dataset is permitted. Do not use `-IncludePowerBI` unless you explicitly intend to publish that embedded data.

The portal description is in `Project_Description_For_Portal.txt` (about 1,100 words, below the 8,000-word limit).
