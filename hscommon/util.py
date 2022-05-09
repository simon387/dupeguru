# Created By: Virgil Dupras
# Created On: 2011-01-11
# Copyright 2015 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from math import ceil
from pathlib import Path
from .path import pathify, log_io_error

from typing import IO, Any, Callable, Generator, Iterable, List, Tuple, Union


def nonone(value: Any, replace_value: Any) -> Any:
    """Returns ``value`` if ``value`` is not ``None``. Returns ``replace_value`` otherwise."""
    if value is None:
        return replace_value
    else:
        return value


def tryint(value: Any, default: int = 0) -> int:
    """Tries to convert ``value`` to in ``int`` and returns ``default`` if it fails."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# --- Sequence related


def dedupe(iterable: Iterable[Any]) -> List[Any]:
    """Returns a list of elements in ``iterable`` with all dupes removed.

    The order of the elements is preserved.
    """
    result = []
    seen = {}
    for item in iterable:
        if item in seen:
            continue
        seen[item] = 1
        result.append(item)
    return result


def flatten(iterables: Iterable[Iterable], start_with: Iterable[Any] = None) -> List[Any]:
    """Takes a list of lists ``iterables`` and returns a list containing elements of every list.

    If ``start_with`` is not ``None``, the result will start with ``start_with`` items, exactly as
    if ``start_with`` would be the first item of lists.
    """
    result: List[Any] = []
    if start_with:
        result.extend(start_with)
    for iterable in iterables:
        result.extend(iterable)
    return result


def first(iterable: Iterable[Any]):
    """Returns the first item of ``iterable``."""
    try:
        return next(iter(iterable))
    except StopIteration:
        return None


def extract(predicate: Callable[[Any], bool], iterable: Iterable[Any]) -> Tuple[List[Any], List[Any]]:
    """Separates the wheat from the shaft (`predicate` defines what's the wheat), and returns both."""
    wheat = []
    shaft = []
    for item in iterable:
        if predicate(item):
            wheat.append(item)
        else:
            shaft.append(item)
    return wheat, shaft


def allsame(iterable: Iterable[Any]) -> bool:
    """Returns whether all elements of 'iterable' are the same."""
    it = iter(iterable)
    try:
        first_item = next(it)
    except StopIteration:
        raise ValueError("iterable cannot be empty")
    return all(element == first_item for element in it)


def iterconsume(seq: List[Any], reverse: bool = True) -> Generator[Any, None, None]:
    """Iterate over ``seq`` and pops yielded objects.

    Because we use the ``pop()`` method, we reverse ``seq`` before proceeding. If you don't need
    to do that, set ``reverse`` to ``False``.

    This is useful in tight memory situation where you are looping over a sequence of objects that
    are going to be discarded afterwards. If you're creating other objects during that iteration
    you might want to use this to avoid ``MemoryError``.
    """
    if reverse:
        seq.reverse()
    while seq:
        yield seq.pop()


# --- String related


def escape(s: str, to_escape: str, escape_with: str = "\\") -> str:
    """Returns ``s`` with characters in ``to_escape`` all prepended with ``escape_with``."""
    return "".join((escape_with + c if c in to_escape else c) for c in s)


def get_file_ext(filename: str) -> str:
    """Returns the lowercase extension part of filename, without the dot."""
    pos = filename.rfind(".")
    if pos > -1:
        return filename[pos + 1 :].lower()
    else:
        return ""


def rem_file_ext(filename: str) -> str:
    """Returns the filename without extension."""
    pos = filename.rfind(".")
    if pos > -1:
        return filename[:pos]
    else:
        return filename


# TODO type hint number
def pluralize(number, word: str, decimals: int = 0, plural_word: Union[str, None] = None) -> str:
    """Returns a pluralized string with ``number`` in front of ``word``.

    Adds a 's' to s if ``number`` > 1.
    ``number``: The number to go in front of s
    ``word``: The word to go after number
    ``decimals``: The number of digits after the dot
    ``plural_word``: If the plural rule for word is more complex than adding a 's', specify a plural
    """
    number = round(number, decimals)
    plural_format = "%%1.%df %%s" % decimals
    if number > 1:
        if plural_word is None:
            word += "s"
        else:
            word = plural_word
    return plural_format % (number, word)


def format_time(seconds: int, with_hours: bool = True) -> str:
    """Transforms seconds in a hh:mm:ss string.

    If ``with_hours`` if false, the format is mm:ss.
    """
    minus = seconds < 0
    if minus:
        seconds *= -1
    m, s = divmod(seconds, 60)
    if with_hours:
        h, m = divmod(m, 60)
        r = "%02d:%02d:%02d" % (h, m, s)
    else:
        r = "%02d:%02d" % (m, s)
    if minus:
        return "-" + r
    else:
        return r


def format_time_decimal(seconds: int) -> str:
    """Transforms seconds in a strings like '3.4 minutes'."""
    minus = seconds < 0
    if minus:
        seconds *= -1
    if seconds < 60:
        r = pluralize(seconds, "second", 1)
    elif seconds < 3600:
        r = pluralize(seconds / 60.0, "minute", 1)
    elif seconds < 86400:
        r = pluralize(seconds / 3600.0, "hour", 1)
    else:
        r = pluralize(seconds / 86400.0, "day", 1)
    if minus:
        return "-" + r
    else:
        return r


SIZE_DESC = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
SIZE_VALS = tuple(1024**i for i in range(1, 9))


def format_size(size: int, decimal: int = 0, forcepower: int = -1, showdesc: bool = True) -> str:
    """Transform a byte count in a formatted string (KB, MB etc..).

    ``size`` is the number of bytes to format.
    ``decimal`` is the number digits after the dot.
    ``forcepower`` is the desired suffix. 0 is B, 1 is KB, 2 is MB etc.. if kept at -1, the suffix
    will be automatically chosen (so the resulting number is always below 1024).
    if ``showdesc`` is ``True``, the suffix will be shown after the number.
    Usage example::

        >>> format_size(1234, decimal=2, showdesc=True)
        '1.21 KB'
    """
    if forcepower < 0:
        i = 0
        while size >= SIZE_VALS[i]:
            i += 1
    else:
        i = forcepower
    if i > 0:
        div = SIZE_VALS[i - 1]
    else:
        div = 1
    size_format = "%%%d.%df" % (decimal, decimal)
    negative = size < 0
    divided_size = (0.0 + abs(size)) / div
    if decimal == 0:
        divided_size = ceil(divided_size)
    else:
        divided_size = ceil(divided_size * (10**decimal)) / (10**decimal)
    if negative:
        divided_size *= -1
    result = size_format % divided_size
    if showdesc:
        result += " " + SIZE_DESC[i]
    return result


def multi_replace(s: str, replace_from: Union[str, List[str]], replace_to: Union[str, List[str]] = "") -> str:
    """A function like str.replace() with multiple replacements.

    ``replace_from`` is a list of things you want to replace. Ex: ['a','bc','d']
    ``replace_to`` is a list of what you want to replace to.
    If ``replace_to`` is a list and has the same length as ``replace_from``, ``replace_from``
    items will be translated to corresponding ``replace_to``. A ``replace_to`` list must
    have the same length as ``replace_from``
    If ``replace_to`` is a string, all ``replace_from`` occurence will be replaced
    by that string.
    ``replace_from`` can also be a str. If it is, every char in it will be translated
    as if ``replace_from`` would be a list of chars. If ``replace_to`` is a str and has
    the same length as ``replace_from``, it will be transformed into a list.
    """
    if isinstance(replace_to, str) and (len(replace_from) != len(replace_to)):
        replace_to = [replace_to for _ in replace_from]
    if len(replace_from) != len(replace_to):
        raise ValueError("len(replace_from) must be equal to len(replace_to)")
    replace = list(zip(replace_from, replace_to))
    for r_from, r_to in [r for r in replace if r[0] in s]:
        s = s.replace(r_from, r_to)
    return s


# --- Files related


@log_io_error
@pathify
def delete_if_empty(path: Path, files_to_delete: List[str] = []) -> bool:
    """Deletes the directory at 'path' if it is empty or if it only contains files_to_delete."""
    if not path.exists() or not path.is_dir():
        return False
    contents = list(path.glob("*"))
    if any(p for p in contents if (p.name not in files_to_delete) or p.is_dir()):
        return False
    for p in contents:
        p.unlink()
    path.rmdir()
    return True


def open_if_filename(
    infile: Union[Path, str, IO],
    mode: str = "rb",
) -> Tuple[IO, bool]:
    """If ``infile`` is a string, it opens and returns it. If it's already a file object, it simply returns it.

    This function returns ``(file, should_close_flag)``. The should_close_flag is True is a file has
    effectively been opened (if we already pass a file object, we assume that the responsibility for
    closing the file has already been taken). Example usage::

        fp, shouldclose = open_if_filename(infile)
        dostuff()
        if shouldclose:
            fp.close()
    """
    if isinstance(infile, Path):
        return (infile.open(mode), True)
    if isinstance(infile, str):
        return (open(infile, mode), True)
    else:
        return (infile, False)


class FileOrPath:
    """Does the same as :func:`open_if_filename`, but it can be used with a ``with`` statement.

    Example::

        with FileOrPath(infile):
            dostuff()
    """

    def __init__(self, file_or_path: Union[Path, str], mode: str = "rb") -> None:
        self.file_or_path = file_or_path
        self.mode = mode
        self.mustclose = False
        self.fp: Union[IO, None] = None

    def __enter__(self) -> IO:
        self.fp, self.mustclose = open_if_filename(self.file_or_path, self.mode)
        return self.fp

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.fp and self.mustclose:
            self.fp.close()
