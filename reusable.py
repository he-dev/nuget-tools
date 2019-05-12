import time

def log_elapsed(func):
    def measure(*args, **kw):
        start = time.perf_counter()
        func(*args, **kw)
        end = time.perf_counter()
        elapsed = round(end - start, 2)
        print(f"'{func.__name__}' elapsed: {elapsed} sec")
    return measure