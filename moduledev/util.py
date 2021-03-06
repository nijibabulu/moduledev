import itertools
import os
import re


def writeable_dir(path):
    """return true if a directory exists and is writeable"""
    return os.path.exists(path) and os.path.isdir(path) and os.access(path, os.W_OK)


def int_or_chr_key(s):
    """Return a sortable value as an integer if possible otherwise, convert the
       character to an integer"""
    try:
        return int(s)
    except Exception:
        return ord(s)


def parse_version_token(s):
    """Return a list of one or two tokens depending on the version token type.
       It is accepted to have a number, a character or a number followed by a
       character, e.g. "5" -> ["5"], "a" -> ["a"] or "5a" -> ["5", "a"] are
       acceptable."""
    if len(s) > 1 and s[-1].isalpha():
        return [s[:-1], s[-1]]
    else:
        return [s]


def tokenize_version(version_string):
    return itertools.chain.from_iterable(
        parse_version_token(t) for t in re.split("\\.|-", version_string)
    )


def version_key(version_string):
    """Return a sortable key for a version. Versions should have their major
       and minor components separated with dots (".") or hyphens ("-") and
       each component may contain a single trailing character, e.g.  1.2.5b > 1.2.5a.
       """

    tokens = tokenize_version(version_string)
    return [int_or_chr_key(t) for t in tokens]


def valid_version(version_string):
    """
    Check if a version string is a valid version string.

    :param version_string: A string
    :return: True if the version string is valid.
    """
    tokens = tokenize_version(version_string)
    for t in tokens:
        try:
            int_or_chr_key(t)
        except TypeError:
            return False
    return True


def valid_package_name(name):
    return re.search(r"[^a-zA-Z0-9_-]", name) is None


def ignore_error(err):
    """Ignore an error"""
    pass


def raise_value_error(err):
    """The default error handler for parse errors. Raises a value error with
    the given error string"""
    raise ValueError(err)
