## windows
```powershell
python -m nuitka `
  --standalone `
  --follow-imports `
  --assume-yes-for-downloads `
  --windows-console-mode=force `
  --output-filename=mping `
  --include-data-file="./README.md=./" `
  --windows-icon-from-ico="./icon/booyaa_multi_ping.ico" `
  ./src/mping/multi_ping.py
```

## linux
```
sudo apt install -y patchelf ccache
python -m nuitka \
  --standalone \
  --follow-imports \
  --follow-stdlib \
  --assume-yes-for-downloads \
  --output-filename=mping \
  --include-data-file="./README.md=./" \
  --include-data-file="~/.local/share/uv/python/cpython-3.13.1-linux-x86_64-gnu/lib/libpython3.13.so.1.0=./" \
  --linux-icon="./icon/booyaa_multi_ping.ico" \
  ./src/mping/multi_ping.py
```
