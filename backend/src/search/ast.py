"""AST node types for a parsed search query."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    """A single filter, e.g. ``c>=rg`` or a bare name word.

    field: normalized filter name ("name", "color", "mv", ...).
    op:    one of ":", "=", "!=", "<", "<=", ">", ">=" (":" is the field's default operator).
    value: the raw right-hand side (already unquoted).
    regex: True when value came from a /.../ literal.
    """

    field: str
    op: str
    value: str
    regex: bool = False


@dataclass(frozen=True)
class Not:
    operand: Node


@dataclass(frozen=True)
class And:
    operands: tuple[Node, ...]


@dataclass(frozen=True)
class Or:
    operands: tuple[Node, ...]


Node = Term | Not | And | Or
