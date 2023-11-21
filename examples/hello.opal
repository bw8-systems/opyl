def main(args: core::Arguments) -> core::ExitCode {
    let hello_world: pstr = "Hello, World!\n"
    core::print(hello_world)
    return core::ExitCode::Success
}