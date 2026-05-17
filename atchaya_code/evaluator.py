from __future__ import annotations
import json
import os
from validation_engine import ValidationEngine


def main() -> None:
    engine = ValidationEngine('rule_mappings_train.json')
    label_path = 'validation_labels_train.json'

    with open(label_path, 'r', encoding='utf-8') as f:
        expected_labels = json.load(f)

    total_rules = 0
    total_matches = 0
    invoice_results = []

    for invoice_id, expected_invoice in expected_labels.items():
        invoice_filename = f"{invoice_id}.xml"
        invoice_path = os.path.join('xml_invoices_train', invoice_filename)
        if not os.path.exists(invoice_path):
            continue
        actual_results = engine.validate_invoice(invoice_path)
        predicted = {rule_id: data['result'] for rule_id, data in actual_results.items()}
        expected = expected_labels.get(invoice_id, {})

        invoice_matches = sum(1 for rule_id, status in predicted.items() if expected.get(rule_id) == status)
        total_matches += invoice_matches
        total_rules += len(predicted)

        invoice_results.append({
            'invoice_id': invoice_id,
            'match_count': invoice_matches,
            'expected_count': len(expected),
            'accuracy': invoice_matches / max(len(predicted), 1)
        })

    overall_accuracy = total_matches / max(total_rules, 1)
    print(f'Validated {len(invoice_results)} invoices against {len(engine.rule_map)} rules.')
    print(f'Overall matching accuracy: {overall_accuracy:.4f}')

    failed = [i for i in invoice_results if i['accuracy'] < 1.0]
    print(f'Invoices with any mismatch: {len(failed)}')


if __name__ == '__main__':
    main()
