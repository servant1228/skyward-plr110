#!/system/bin/sh
# For the PLR110 diagnostic ramdisk only. Wait for Skyward's slot mounts.
PATH=/system/bin
export PATH
note() { echo "<6>skyward-touch: $*" > /dev/kmsg; }
fail() { note "$*"; exit 1; }
i=0
while ! grep -q ' /vendor erofs ' /proc/mounts || ! grep -q ' /odm erofs ' /proc/mounts; do
    [ "$i" -lt 45 ] || fail 'slot mounts unavailable; touch service not requested'
    sleep 1
    i=$((i+1))
done
fw=/vendor/firmware
cfg=tp/macan/vnd_touch_project_config.xml
[ -r "/odm/firmware/$cfg" ] || fail 'installed macan touch configuration missing'
if [ ! -r "$fw/$cfg" ]; then
    # Keep every existing vendor file. The extra lower directory contains only
    # one symlink, tp -> /odm/firmware/tp. No upperdir or writable partition.
    mount -t overlay -o "ro,nosuid,nodev,lowerdir=/skyward/firmware-extra:$fw" overlay "$fw" || fail 'read-only firmware overlay failed'
fi
[ -r "$fw/$cfg" ] && [ -r "$fw/tp/macan/vnd_tp_fw_main.bin" ] || fail 'touch files not visible after mount'
setprop vendor.firmware.tp.copy 1 || fail 'init refused touch firmware ready signal'
note 'macan firmware ready; requested OEM touch startup'
