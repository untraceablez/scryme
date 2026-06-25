"""Lexer/parser unit tests: tokenization, atom decoding, boolean structure, errors."""

import pytest
from src.search.ast import And, Not, Or, Term
from src.search.errors import SearchError
from src.search.parser import atom_to_term, parse


def test_bare_word_is_name_search():
    assert atom_to_term("goblin") == Term("name", ":", "goblin", False)


def test_keyed_filters_and_aliases():
    assert atom_to_term("c:r") == Term("color", ":", "r", False)
    assert atom_to_term("color:rg") == Term("color", ":", "rg", False)
    assert atom_to_term("cmc>=3") == Term("mv", ">=", "3", False)
    assert atom_to_term("t:creature") == Term("type", ":", "creature", False)
    assert atom_to_term("e:mh2") == Term("set", ":", "mh2", False)


def test_quoted_value_is_unwrapped():
    assert atom_to_term('name:"Black Lotus"') == Term("name", ":", "Black Lotus", False)


def test_operators():
    assert atom_to_term("mv!=2") == Term("mv", "!=", "2", False)
    assert atom_to_term("pow<=1") == Term("power", "<=", "1", False)
    assert atom_to_term("usd>5") == Term("usd", ">", "5", False)


def test_bare_regex_is_name():
    t = atom_to_term("/^Gob/")
    assert t == Term("name", "~", "^Gob", True)


def test_keyed_regex():
    t = atom_to_term("o:/draw a card/")
    assert t == Term("oracle", "~", "draw a card", True)


def test_unknown_filter_raises():
    with pytest.raises(SearchError):
        atom_to_term("bogus:value")


def test_parse_implicit_and():
    node = parse("c:r t:instant")
    assert isinstance(node, And)
    assert len(node.operands) == 2


def test_parse_or():
    node = parse("c:r OR c:u")
    assert isinstance(node, Or)


def test_parse_negation():
    node = parse("-t:creature")
    assert isinstance(node, Not)
    assert node.operand == Term("type", ":", "creature", False)


def test_parse_parentheses_grouping():
    node = parse("(c:r OR c:u) t:instant")
    assert isinstance(node, And)
    assert isinstance(node.operands[0], Or)


def test_parse_empty_is_none():
    assert parse("") is None
    assert parse("   ") is None


def test_unbalanced_parens_raise():
    with pytest.raises(SearchError):
        parse("(c:r")
    with pytest.raises(SearchError):
        parse("c:r)")
