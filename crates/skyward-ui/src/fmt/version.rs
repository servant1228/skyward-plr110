/// A version label for the UI only. OTA and restore checks must use the raw value.
pub fn os_version(raw: &str) -> &str {
    let version = raw.trim_end();
    for tag in ["release-keys", "test-keys", "dev-keys"] {
        if let Some(prefix) = version.strip_suffix(tag)
            && prefix.ends_with([' ', '\t', '-'])
        {
            return prefix.trim_end_matches([' ', '\t', '-']);
        }
    }
    version.strip_suffix("-keys").filter(|v| !v.is_empty() && !matches!(*v, "release" | "test" | "dev")).unwrap_or(version)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hides_only_a_trailing_build_tag_or_keys_suffix() {
        for (input, expected) in [
            ("BP2A.250605.015 release-keys", "BP2A.250605.015"),
            ("17.0.0.101(CN01)-keys", "17.0.0.101(CN01)"),
            ("build-test-keys", "build"), ("build dev-keys  ", "build"),
            ("17.0.0.101(CN01)", "17.0.0.101(CN01)"),
            ("build-keys-beta", "build-keys-beta"), ("release-keys", "release-keys"), ("", ""),
        ] {
            assert_eq!(os_version(input), expected);
        }
    }
}
