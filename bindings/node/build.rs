use std::process::Command;

fn main() {
    napi_build::setup();
    // Reproducible builds pass the commit explicitly; otherwise ask git.
    println!("cargo:rerun-if-env-changed=PDFUST_GIT_SHA");
    let sha = std::env::var("PDFUST_GIT_SHA")
        .ok()
        .filter(|value| !value.is_empty())
        .or_else(|| {
            Command::new("git")
                .args(["rev-parse", "HEAD"])
                .output()
                .ok()
                .filter(|output| output.status.success())
                .and_then(|output| String::from_utf8(output.stdout).ok())
                .map(|value| value.trim().to_owned())
        })
        .unwrap_or_else(|| "unknown".to_owned());
    println!("cargo:rustc-env=PDFUST_GIT_SHA={sha}");
}
