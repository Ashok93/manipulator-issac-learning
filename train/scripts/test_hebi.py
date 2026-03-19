import subprocess
result = subprocess.run(
    ["nm", "-D", "/workspace/train/.venv/lib/python3.12/site-packages/hebi/lib/linux_x86_64/libhebi.so.2.21"],
    capture_output=True, text=True
)
for line in result.stdout.splitlines():
    if "ookup" in line.lower() or "ddress" in line.lower():
        print(line)
