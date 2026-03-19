import hebi
import ctypes
import time

lookup = hebi.Lookup()

lib = ctypes.CDLL(
    "/workspace/train/.venv/lib/python3.12/site-packages/hebi/lib/linux_x86_64/libhebi.so.2.21"
)
lib.hebiLookupAddAddress(lookup._Lookup__delegate, b"100.117.87.101")

time.sleep(2)

group = lookup.get_group_from_names(["HEBI"], ["mobileIO"])
print("Found!" if group else "Not found")
