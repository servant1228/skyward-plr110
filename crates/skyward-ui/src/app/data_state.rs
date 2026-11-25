/// Which control answers a user's screen lock, by the kind of lock it is.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Keys {
    Pattern,
    Digits,
    Letters,
}

/// Where the data partition stands.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub enum Data {
    /// Not opened; the decrypt page opens it as it shows.
    #[default]
    Closed,
    /// Being opened as far as it opens with nothing a user knows, which is
    /// also when each user's screen lock is read.
    Opening,
    /// Open, with this user's own files waiting on their screen lock,
    /// answered with `keys`; `checking` while what they entered is checked.
    Locked { user: u32, keys: Keys, checking: bool },
    /// Open, every user's own files with it.
    Open,
    /// The partition is mounted, but opening all users did not finish.
    /// Only confirmed access to the owner's shared storage is exposed.
    Incomplete { owner_storage: bool, why: String },
    /// Not opened, and why.
    Failed(String),
    /// Erased whole: nothing opens until the system makes it afresh, as it
    /// next starts.
    Erased,
}

impl Data {
    /// Re-entering a mounted, incomplete result only displays it. An
    /// explicit retry is distinct from navigating back to this page.
    pub fn open_on_entry(&self) -> bool {
        matches!(self, Self::Closed | Self::Failed(_))
    }

    /// Whether the owner's internal storage can be read: the partition is
    /// open, and so are the owner's own files, which open first.
    pub fn storage_open(&self) -> bool {
        match self {
            Data::Open => true,
            Data::Incomplete { owner_storage, .. } => *owner_storage,
            // The owner is user 0.
            Data::Locked { user, .. } => *user != 0,
            _ => false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn incomplete_opening_exposes_only_confirmed_owner_storage() {
        for confirmed in [false, true] {
            let d = Data::Incomplete { owner_storage: confirmed, why: "user 10: Weaver unavailable".into() };
            assert_eq!(d.storage_open(), confirmed);
            assert!(!d.open_on_entry());
            assert_ne!(d, Data::Open); // Whole-data backups still require Open.
        }
    }

    #[test]
    fn a_mount_failure_still_retries_and_does_not_expose_storage() {
        for d in [Data::Closed, Data::Failed("mount failed".into())] {
            assert!(d.open_on_entry());
            assert!(!d.storage_open());
        }
        assert!(!Data::Open.open_on_entry());
        assert!(Data::Open.storage_open());
    }

    #[test]
    fn a_real_credential_prompt_is_not_a_service_failure() {
        for user in [0, 10] {
            let d = Data::Locked { user, keys: Keys::Digits, checking: false };
            assert_eq!(d.storage_open(), user != 0);
            assert!(!d.open_on_entry());
        }
    }
}
