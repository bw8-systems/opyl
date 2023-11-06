#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>

typedef struct _NoneType
{
} _NoneType;

_NoneType _None;

typedef enum OptionTag
{
    Option_Some,
    Option_None
} OptionTag;

typedef struct Range
{
    uint32_t start;
    uint32_t stop;
    uint32_t current;
} Range;

typedef struct Option_u32
{
    OptionTag tag;
    union
    {
        _NoneType none;
        uint32_t some;
    } value;
} Option_u32;

Range Range_new(uint32_t start, uint32_t stop)
{
    Range range = {
        .start = start,
        .stop = stop,
        .current = start,
    };

    return range;
}

Option_u32 Range_next(Range *self)
{
    Option_u32 option = {
        .tag = Option_None,
        .value = {.none = _None},
    };

    if (self->current < self->stop)
    {
        option.tag = Option_Some;
        option.value.some = self->current;

        self->current += 1;

        return option;
    }

    return option;
}

uint32_t fibonacci(uint32_t n)
{
    if (n == 0)
    {
        return 1;
    }

    if (n == 1)
    {
        return 1;
    }

    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main(int argc, char *argv[])
{
    Range range = Range_new(0, 10);
    Option_u32 item;

    while (1)
    {
        item = Range_next(&range);
        if (item.tag == Option_None)
        {
            break;
        }

        printf("%d\n", fibonacci(item.value.some));
    }

    return EXIT_SUCCESS;
}