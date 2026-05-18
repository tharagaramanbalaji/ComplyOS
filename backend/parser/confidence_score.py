class ConfidenceScore:
    def calculate(self, rule_text: str, intent: str, ir_node) -> float:
        score = 0.0
        
        if intent != "unknown":
            score += 0.4
            
        if ir_node and ir_node.type != "unknown":
            score += 0.4
            
            # Check if required fields for the intent are present
            if ir_node.type == "conditional_required_field" and hasattr(ir_node, "condition") and hasattr(ir_node, "required_field"):
                score += 0.2
            elif ir_node.type == "numeric_comparison" and hasattr(ir_node, "field") and hasattr(ir_node, "operator") and hasattr(ir_node, "value"):
                score += 0.2
            elif ir_node.type == "required_field" and hasattr(ir_node, "field"):
                score += 0.2
            elif ir_node.type == "date_validation" and hasattr(ir_node, "field"):
                score += 0.2
            elif ir_node.type == "duplicate_field_check" and hasattr(ir_node, "field"):
                score += 0.2
            else:
                score += 0.1
        
        return min(score, 1.0)
