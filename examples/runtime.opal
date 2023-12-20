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
            is char { return 0 }
            else { ... }
        }

        if self is char {
            ...
        }
    }
}

def print[T: Printable](value: T) {
    value.print()
}
