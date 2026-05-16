from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field

# Base Rule class
class BaseRule(BaseModel):
    rule_type: str

# 1. Required Field Schema
class RequiredFieldRule(BaseRule):
    rule_type: Literal["required_field"]
    field: str
    check: Literal["is_present"]

# 2. Conditional Required Field Schema
class Condition(BaseModel):
    field: str
    operator: str
    value: str

class Action(BaseModel):
    field: str
    check: Literal["is_present"]

class ConditionalRequiredFieldRule(BaseRule):
    rule_type: Literal["conditional_required_field"]
    condition: Condition
    action: Action

# 3. Date Validation Schema
class DateValidationRule(BaseRule):
    rule_type: Literal["date_validation"]
    field: str
    operator: Literal["<="]
    value: Literal["CURRENT_DATE"]

# 4. Numeric Comparison Schema
class NumericComparisonRule(BaseRule):
    rule_type: Literal["numeric_comparison"]
    field: str
    operator: Literal[">="]
    value: Union[int, float]

# 5. Amount Calculation Schema
class AmountCalculationRule(BaseRule):
    rule_type: Literal["amount_calculation"]
    field: str
    equation: Optional[str] = None
    aggregation: Optional[Literal["sum"]] = None
    expected_match: Optional[str] = None

# 6. Currency Consistency Schema
class CurrencyConsistencyRule(BaseRule):
    rule_type: Literal["currency_consistency"]
    field: str
    expected_match: str

# 7. Tax Category Validation Schema
class TaxCategoryValidationRule(BaseRule):
    rule_type: Literal["tax_category_validation"]
    field: str
    valid_values: List[str]

# 8. Duplicate Field Check Schema
class DuplicateFieldCheckRule(BaseRule):
    rule_type: Literal["duplicate_field_check"]
    field: str
    check: Literal["is_unique_globally"]

# A Union type to parse any incoming rule correctly based on rule_type
AnyRule = Union[
    RequiredFieldRule,
    ConditionalRequiredFieldRule,
    DateValidationRule,
    NumericComparisonRule,
    AmountCalculationRule,
    CurrencyConsistencyRule,
    TaxCategoryValidationRule,
    DuplicateFieldCheckRule
]
