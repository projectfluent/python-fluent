import os


# Unify path separator, default path separator on Windows is \ not /
# Needed in test_falllback.py because it uses dict + string compare to make a virtual file structure
def normalize_path(path):
    return "/".join(os.path.split(path))
