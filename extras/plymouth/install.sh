#!/bin/bash
# Install the Iron Man arc-reactor disk-unlock screen (Plymouth).
#
#   sudo bash extras/plymouth/install.sh
#
# Undo (back to Omarchy's own screen):
#   sudo bash extras/plymouth/install.sh --undo
#
# Uses the same steps as omarchy-plymouth-set: select the theme, then rebuild
# the boot images with limine-mkinitcpio (or mkinitcpio -P without Limine).
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
DEST=/usr/share/plymouth/themes/ironman

[[ $EUID -eq 0 ]] || { echo "Run with sudo."; exit 1; }

rebuild() {
  if command -v limine-mkinitcpio >/dev/null; then limine-mkinitcpio; else mkinitcpio -P; fi
}

if [[ ${1:-} == --undo ]]; then
  plymouth-set-default-theme omarchy
  rebuild
  echo "Back to the Omarchy unlock screen. Reboot to see it."
  exit 0
fi

for f in ironman.plymouth ironman.script entry.png bullet.png lock.png idle-00.png boot-00.png; do
  [[ -f $HERE/theme/$f ]] || { echo "Missing theme file: $f"; exit 1; }
done

avail_mb=$(df -Pm /boot | awk 'NR==2 {print $4}')
(( avail_mb > 200 )) || { echo "Only ${avail_mb} MB free in /boot - not installing."; exit 1; }

previous=$(plymouth-set-default-theme)
echo "Current theme: $previous"
install -d "$DEST"
install -m 644 "$HERE"/theme/* "$DEST"/
echo "Installed $(ls "$DEST" | wc -l) files to $DEST"

plymouth-set-default-theme ironman
if ! rebuild; then
  echo "Rebuild failed - restoring the '$previous' theme." >&2
  plymouth-set-default-theme "$previous"
  rebuild
  exit 1
fi
echo "Theme now: $(plymouth-set-default-theme). Reboot to see it."
echo "Undo any time: sudo bash $HERE/install.sh --undo"
