use std::time::Duration;

/// Retry only the link operation, only while the error is transient. A zero
/// budget preserves single-shot behavior; keep the final kernel error intact.
pub(super) fn while_busy<T, E>(
    mut up: impl FnMut() -> Result<T, E>,
    busy: impl Fn(&E) -> bool,
    mut remaining: impl FnMut() -> Duration,
    mut sleep: impl FnMut(Duration),
) -> Result<T, E> {
    loop {
        match up() {
            Err(e) if busy(&e) => {
                let delay = remaining().min(Duration::from_millis(200));
                if delay.is_zero() { return Err(e); }
                sleep(delay);
            }
            result => return result,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::Cell;

    fn simulate(results: &[Result<(), i32>], ms: u64) -> (Result<(), i32>, usize, u64) {
        let elapsed = Cell::new(0);
        let mut calls = 0;
        let res = while_busy(|| { let r = results[calls]; calls += 1; r }, |e| *e == 16,
            || Duration::from_millis(ms - elapsed.get()), |d| elapsed.set(elapsed.get() + d.as_millis() as u64));
        (res, calls, elapsed.get())
    }

    #[test] fn already_ready() { assert_eq!(simulate(&[Ok(())], 5000), (Ok(()), 1, 0)); }
    #[test] fn transient_busy() { assert_eq!(simulate(&[Err(16), Err(16), Ok(())], 5000), (Ok(()), 3, 400)); }
    #[test] fn bounded() { assert_eq!(simulate(&[Err(16); 3], 250), (Err(16), 3, 250)); }
    #[test] fn no_budget() { assert_eq!(simulate(&[Err(16)], 0), (Err(16), 1, 0)); }
    #[test] fn other_errors_propagate() { assert_eq!(simulate(&[Err(16), Err(1)], 5000), (Err(1), 2, 200)); }
}
