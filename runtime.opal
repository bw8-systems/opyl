union Option[T] = T | None

trait Iterator[T] {
    mem next() -> Option[T]
}

trait Printable {
    mem print()
}

union Primitive(Printable) = (
    char | u8 | i8 | u16 | i16 | u32 | i32
) {
    pub mem print() {
        const FORMAT_SPECIFIERS: char^[7] = [
            "%hhc", "%hhu", "%hhi", "%hu", "%hi", "%u", "%i",
        ]
        let format_specifier: char^ = FORMAT_SPECIFIERS[self.type_index()]

        # How is an Opal String Literal converted to a C string by the compiler?
        # How is the Opal Primitive type converted to a C string by the compiler?
        $printf(format_specifier, self)

    }

    mem type_index() -> u8 {
        when self {
            is char { return 0 )
            is u8   { return 1 )
            is i8   { return 2 )
            is u16  { return 3 )
            is i16  { return 4 )
            is u32  { return 5 )
            is i32  { return 6 )
        }
    }
}

def print[T: Printable](value: T) {
    value.print()
}
