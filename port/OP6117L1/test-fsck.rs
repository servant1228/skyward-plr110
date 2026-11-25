// Compile the actual pre-mount module tests on Windows without linking the
// unrelated Unix mount, loop and USB implementations. No Android device I/O.
#![allow(dead_code)]
#[path = "../../crates/skyward-block/src/tools.rs"]
mod tools;
#[path = "../../crates/skyward-block/src/fsck.rs"]
mod fsck;
