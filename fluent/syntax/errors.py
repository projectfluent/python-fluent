
def get_error_slice(source, start, end):
    length = len(source)

    start_pos = None
    slice_len = end - start

    if length < slice_len:
        start_pos = 0
        slice_len = len
    elif start + slice_len >= length:
        start_pos = length - slice_len - 1
    else:
        start_pos = start

    slice = None

    if start_pos > 0:
        slice = source[start_pos - 1:start_pos - 1 + slice_len]
    else:
        slice = source[0:slice_len]
    return slice
