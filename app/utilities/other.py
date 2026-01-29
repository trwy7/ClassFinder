"""
This module contains utility functions that do not fit into any other category.
"""
import re
def split_list(lst: list, n: int):
    """
    Split a list into sublists of length n.

    Args:
        lst (list): The list to split.
        n (int): The length of each sublist.

    Returns:
        list: A list of sublists.
    """
    return [lst[i : i + n] for i in range(0, len(lst), n)]

def optimize_css(css: str) -> str:
    """
    Optimize CSS by removing comments and unnecessary whitespace.

    Args:
        css (str): The CSS string to optimize.
    Returns:
        str: The optimized CSS string.
    """

    # Remove comments
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    # Remove unnecessary whitespace
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r'\s*([{};:,])\s*', r'\1', css)
    css = css.strip()
    return css
