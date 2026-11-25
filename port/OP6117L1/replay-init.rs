//! Standalone host-side check of the production parser against OEM rc files, without running their commands.
#[path = "../../crates/skyward-programs/src/script.rs"]
mod script;
use std::{fs, path::Path};
fn visit(dir: &Path, count: &mut usize, bad: &mut usize) -> std::io::Result<()> {
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        if entry.file_type()?.is_dir() { visit(&entry.path(), count, bad)?; }
        else if entry.path().extension().and_then(|s| s.to_str()) == Some("rc") {
            *count += 1;
            let path = entry.path();
            if let Err(e) = script::read(&fs::read_to_string(&path)?) {
                eprintln!("{}: {e:#}", path.display()); *bad += 1;
            }
        }
    }
    Ok(())
}
fn main() -> std::io::Result<()> {
    let (mut count, mut bad) = (0, 0);
    visit(Path::new(&std::env::args_os().nth(1).expect("provide an rc directory")), &mut count, &mut bad)?;
    println!("parsed {count} files, {bad} errors");
    if count == 0 || bad > 0 { std::process::exit(1) }
    Ok(())
}
