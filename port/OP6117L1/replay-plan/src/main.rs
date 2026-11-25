//! Host-only test of the startup plan. No HAL or credential operations are invoked.
#![allow(dead_code)]
// The planner needs only this name from the Android-only Binder implementation.
extern crate self as skyward_omapi;
pub const SERVICE: &str = "android.se.omapi.ISecureElementService/default";
#[path = "../../../../crates/skyward-programs/src/description.rs"] mod description;
#[path = "../../../../crates/skyward-programs/src/script.rs"] mod script;
#[path = "../../../../crates/skyward-programs/src/phone.rs"] mod phone;
#[path = "../../../../crates/skyward-programs/src/secure.rs"] mod secure;

fn main() -> anyhow::Result<()> {
    let root = std::path::PathBuf::from(std::env::args_os().nth(1).expect("path to OEM rc, vintf and executable-name snapshot"));
    let props = [("ro.boot.hardware", "qcom"), ("ro.boot.product.vendor.sku", "alor"), ("ro.boot.product.hardware.sku", "7")];
    let parts = phone::PARTITIONS.iter().map(|&name| phone::Partition { name: name.into(), mounted: format!("/{name}").into(), at: root.join(name) }).collect();
    let oem = phone::Phone::read(parts, props.map(|(k,v)| (k.into(), v.into())).into_iter().collect(), None)?;
    println!("{} described AIDL services", oem.told_of().len());
    let plan = secure::steps(&oem)?;
    let mut names = Vec::new();
    for step in plan {
        match step {
            secure::Step::Start(s) => names.push(s.service.path.replace('\\', "/")),
            secure::Step::Drive(d) => names.push(format!("{} => {}", d.module, d.node)),
            secure::Step::ServeElements => names.push(SERVICE.into()),
        }
    }
    for n in &names { println!("{n}"); }
    let mut names = names.iter();
    for expected in ["/vendor/bin/qseecomd", "/vendor/bin/hw/android.hardware.security.onekeymint-service-qti", "nxp-nci => /dev/nq-nci", "/odm/bin/hw/android.hardware.secure_element-service.qti", SERVICE, "/odm/bin/hw/android.hardware.weaver-service.nxp"] {
        anyhow::ensure!(names.any(|n| n == expected), "missing or out of order: {expected}");
    }
    Ok(())
}
