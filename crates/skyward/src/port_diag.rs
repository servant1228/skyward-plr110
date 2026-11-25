//! Early startup evidence for the local OP6117L1 diagnostic image.
use std::{fs, io::Write, os::unix::fs::OpenOptionsExt, path::Path};

pub(crate) fn mark(stage: &str) {
    if !Path::new("/skyward/port-diagnostics").exists() { return; }
    let Ok(mounts) = fs::read_to_string("/proc/mounts") else { return };
    for (mount, log) in [("/cache", "/cache/recovery/skyward-startup.log"), ("/metadata", "/metadata/skyward-startup.log")] {
        let writable = mounts.lines().any(|line| {
            let mut cols = line.split_whitespace().skip(1);
            cols.next() == Some(mount) && matches!(cols.next(), Some("ext4" | "f2fs")) &&
                cols.next().is_some_and(|options| options.split(',').any(|opt| opt == "rw"))
        });
        if !writable { continue; }
        if let Ok(mut file) = fs::OpenOptions::new().create(true).append(true).mode(0o600)
            .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK).open(log) {
            if !file.metadata().is_ok_and(|m| m.is_file() && m.len() < 65536) { continue; }
            let uptime = fs::read_to_string("/proc/uptime").unwrap_or_default();
            let message: String = stage.chars().filter(|c| !c.is_control()).take(512).collect();
            if writeln!(file, "[{}] pid={} {message}", uptime.split_whitespace().next().unwrap_or("?"), std::process::id()).is_ok() && file.sync_data().is_ok() { return; }
        }
    }
}
