from __future__ import annotations
from typing import Literal, Optional, Union
from pydantic import BaseModel


class BaseRule(BaseModel):
    rule_type: str
    severity: Optional[str] = None


class Condition(BaseModel):
    field: str
    operator: Literal['==', '!=', '<', '<=', '>', '>=']
    value: str


class Action(BaseModel):
    field: str
    check: Literal['is_present']


class RequiredFieldRule(BaseRule):
    rule_type: Literal['required_field']
    field: str
    check: Literal['is_present']


class ConditionalRequiredFieldRule(BaseRule):
    rule_type: Literal['conditional_required_field']
    condition: Condition
    action: Action


class DateValidationRule(BaseRule):
    rule_type: Literal['date_validation']
    field: str
    operator: Literal['<=', '<', '>=', '>']
    value: str


class NumericComparisonRule(BaseRule):
    rule_type: Literal['numeric_comparison']
    field: str
    operator: Literal['>=', '<=', '>', '<', '==', '!=']
    value: float


class AmountCalculationRule(BaseRule):
    rule_type: Literal['amount_calculation']
    field: str
    aggregation: Optional[Literal['sum']] = None
    expected_match: Optional[str] = None
    equation: Optional[str] = None


class CurrencyConsistencyRule(BaseRule):
    rule_type: Literal['currency_consistency']
    field: str
    expected_match: str


class TaxCategoryValidationRule(BaseRule):
    rule_type: Literal['tax_category_validation']
    field: str
    valid_values: Optional[list[str]] = None


class DuplicateFieldCheckRule(BaseRule):
    rule_type: Literal['duplicate_field_check']
    field: str
    check: Literal['is_unique_globally']


RuleModel = Union[
    RequiredFieldRule,
    ConditionalRequiredFieldRule,
    DateValidationRule,
    NumericComparisonRule,
    AmountCalculationRule,
    CurrencyConsistencyRule,
    TaxCategoryValidationRule,
    DuplicateFieldCheckRule,
]
