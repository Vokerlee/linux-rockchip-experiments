import os

def build_random_copy(params):
    for arr_size, shift in sorted(params):
        os.system(f'make ARRAY_SIZE_LOG2={arr_size} SHIFT_LOG2={shift} POSTFIX={arr_size}_{shift}')

def get_params_list():
    params_list = []

    for arr_log2 in range(10, 30):
        for shift_log2 in range(4, 7):
            params_list.append((arr_log2, shift_log2))

        for shift_log2 in range(7, arr_log2 - 1, 4):
            params_list.append((arr_log2, shift_log2))

    return params_list

if __name__ == "__main__":
    build_random_copy(get_params_list())
