"""Rule definitions and deterministic scoring engine for document classification."""

from typing import Dict, List, Set, Tuple
from pydantic import BaseModel, Field

from tools.classifier.constants import DocumentType
from tools.parser.models import ParsedDocument


class DocumentRule(BaseModel):
    """Rule definition for evaluating a specific document type."""

    doc_type: str
    primary_keywords: Set[str] = Field(default_factory=set)
    secondary_keywords: Set[str] = Field(default_factory=set)
    table_headers: Set[str] = Field(default_factory=set)
    negative_keywords: Set[str] = Field(default_factory=set)


# Deterministic rule repository for supported business document types
CLASSIFICATION_RULES: List[DocumentRule] = [
    DocumentRule(
        doc_type=DocumentType.GST_INVOICE,
        primary_keywords={"TAX INVOICE", "GST INVOICE", "GSTIN", "CGST", "SGST", "IGST"},
        secondary_keywords={"HSN/SAC", "HSN CODE", "BILL TO", "SHIP TO", "TAXABLE VALUE", "PLACE OF SUPPLY"},
        table_headers={"HSN", "SAC", "RATE", "TAXABLE VALUE", "CGST", "SGST", "IGST"},
    ),
    DocumentRule(
        doc_type=DocumentType.SALES_INVOICE,
        primary_keywords={"SALES INVOICE", "INVOICE", "BILL OF SUPPLY"},
        secondary_keywords={"INVOICE NUMBER", "INVOICE DATE", "DUE DATE", "BILL TO", "TOTAL AMOUNT"},
        table_headers={"ITEM", "DESCRIPTION", "QUANTITY", "QTY", "PRICE", "AMOUNT"},
        negative_keywords={"PURCHASE ORDER", "BANK STATEMENT"},
    ),
    DocumentRule(
        doc_type=DocumentType.PURCHASE_INVOICE,
        primary_keywords={"PURCHASE INVOICE", "VENDOR INVOICE", "SUPPLIER INVOICE"},
        secondary_keywords={"VENDOR GSTIN", "PO NUMBER", "BILLING ADDRESS", "PAYMENT TERMS"},
        table_headers={"ITEM DESCRIPTION", "UNIT PRICE", "TOTAL"},
    ),
    DocumentRule(
        doc_type=DocumentType.PURCHASE_ORDER,
        primary_keywords={"PURCHASE ORDER", "PO NUMBER", "P.O. NO"},
        secondary_keywords={"ORDER DATE", "DELIVERY DATE", "VENDOR NAME", "SHIP TO ADDRESS", "TERMS & CONDITIONS"},
        table_headers={"ITEM CODE", "QTY ORDERED", "UNIT PRICE", "NET AMOUNT"},
        negative_keywords={"INVOICE"},
    ),
    DocumentRule(
        doc_type=DocumentType.QUOTATION,
        primary_keywords={"QUOTATION", "PROFORMA INVOICE", "QUOTE", "ESTIMATE"},
        secondary_keywords={"VALID UNTIL", "QUOTE NUMBER", "PROPOSAL", "TERMS OF PAYMENT"},
        table_headers={"SPECIFICATION", "UNIT RATE", "TOTAL ESTIMATE"},
    ),
    DocumentRule(
        doc_type=DocumentType.SALES_ORDER,
        primary_keywords={"SALES ORDER", "SO NUMBER", "ORDER CONFIRMATION"},
        secondary_keywords={"CUSTOMER PO", "BOOKING DATE", "DISPATCH THROUGH"},
        table_headers={"ORDERED QTY", "RATE", "AMOUNT"},
    ),
    DocumentRule(
        doc_type=DocumentType.CREDIT_NOTE,
        primary_keywords={"CREDIT NOTE", "CREDIT MEMO"},
        secondary_keywords={"ORIGINAL INVOICE NO", "REASON FOR CREDIT", "ADJUSTMENT AMOUNT"},
        negative_keywords={"DEBIT NOTE"},
    ),
    DocumentRule(
        doc_type=DocumentType.DEBIT_NOTE,
        primary_keywords={"DEBIT NOTE", "DEBIT MEMO"},
        secondary_keywords={"ORIGINAL INVOICE NO", "REASON FOR DEBIT", "CHARGES"},
        negative_keywords={"CREDIT NOTE"},
    ),
    DocumentRule(
        doc_type=DocumentType.DELIVERY_CHALLAN,
        primary_keywords={"DELIVERY CHALLAN", "DISPATCH CHALLAN", "WAYBILL"},
        secondary_keywords={"VEHICLE NO", "DRIVER NAME", "MODE OF TRANSPORT", "NOT FOR SALE"},
        table_headers={"DISPATCHED QTY", "PACKAGES"},
    ),
    DocumentRule(
        doc_type=DocumentType.GOODS_RECEIPT_NOTE,
        primary_keywords={"GOODS RECEIPT NOTE", "GRN", "MATERIAL RECEIPT"},
        secondary_keywords={"RECEIVED BY", "INSPECTED BY", "PO REF", "ACCEPTED QTY", "REJECTED QTY"},
    ),
    DocumentRule(
        doc_type=DocumentType.RECEIPT,
        primary_keywords={"RECEIPT", "PAYMENT RECEIPT", "MONEY RECEIPT"},
        secondary_keywords={"RECEIVED WITH THANKS", "MODE OF PAYMENT", "CHEQUE NO", "TRANSACTION ID"},
    ),
    DocumentRule(
        doc_type=DocumentType.PAYMENT_VOUCHER,
        primary_keywords={"PAYMENT VOUCHER", "DEBIT VOUCHER"},
        secondary_keywords={"PAID TO", "BEING THE PAYMENT OF", "ACCOUNT HEAD", "APPROVED BY"},
    ),
    DocumentRule(
        doc_type=DocumentType.EXPENSE_BILL,
        primary_keywords={"EXPENSE BILL", "PETTY CASH VOUCHER", "REIMBURSEMENT"},
        secondary_keywords={"EMPLOYEE NAME", "EXPENSE TYPE", "CLAIM AMOUNT"},
    ),
    DocumentRule(
        doc_type=DocumentType.BANK_STATEMENT,
        primary_keywords={"BANK STATEMENT", "STATEMENT OF ACCOUNT", "ACCOUNT STATEMENT"},
        secondary_keywords={"ACCOUNT NUMBER", "IFS CODE", "OPENING BALANCE", "CLOSING BALANCE", "WITHDRAWAL", "DEPOSIT"},
        table_headers={"DATE", "PARTICULARS", "CHQ NO", "WITHDRAWAL", "DEPOSIT", "BALANCE"},
    ),
    DocumentRule(
        doc_type=DocumentType.GST_RETURN,
        primary_keywords={"GSTR-1", "GSTR-3B", "GST RETURN", "ACKNOWLEDGEMENT NUMBER"},
        secondary_keywords={"TAX PERIOD", "ARN", "FILED DATE", "TURNOVER"},
    ),
    DocumentRule(
        doc_type=DocumentType.SALARY_SLIP,
        primary_keywords={"SALARY SLIP", "PAYSLIP", "PAY SLIP"},
        secondary_keywords={"EMPLOYEE ID", "DESIGNATION", "PAN NUMBER", "BASIC SALARY", "PF NO", "NET PAY", "GROSS EARNINGS"},
        table_headers={"EARNINGS", "DEDUCTIONS", "AMOUNT"},
    ),
]


class RuleEngine:
    """Evaluates ParsedDocument against classification rules deterministically."""

    @staticmethod
    def evaluate(parsed_doc: ParsedDocument) -> Tuple[str, float, List[str], str]:
        """Evaluates document text and table headers against rules.

        Returns:
            Tuple containing (best_doc_type, confidence_score, matched_rule_signals, reason)
        """
        # Combine all extracted text into uppercase for case-insensitive matching
        text_corpus = "\n".join(page.text for page in parsed_doc.pages).upper()

        # Extract table headers in uppercase
        table_headers_set: Set[str] = set()
        for table in parsed_doc.tables:
            for header in table.headers:
                table_headers_set.add(header.upper())

        best_doc_type = DocumentType.UNKNOWN
        highest_score = 0.0
        best_signals: List[str] = []
        best_reason = "Insufficient rule matches."

        for rule in CLASSIFICATION_RULES:
            score = 0.0
            matched_signals: List[str] = []

            # 1. Check Negative Keywords
            negative_triggered = False
            for neg in rule.negative_keywords:
                if neg in text_corpus:
                    negative_triggered = True
                    break
            if negative_triggered:
                continue

            # 2. Score Primary Keywords (Weight: 0.4 each)
            for primary in rule.primary_keywords:
                if primary in text_corpus:
                    score += 0.4
                    matched_signals.append(f"Primary: '{primary}'")

            # 3. Score Secondary Keywords (Weight: 0.15 each)
            for secondary in rule.secondary_keywords:
                if secondary in text_corpus:
                    score += 0.15
                    matched_signals.append(f"Secondary: '{secondary}'")

            # 4. Score Table Headers (Weight: 0.2 each)
            for req_header in rule.table_headers:
                if any(req_header in h for h in table_headers_set):
                    score += 0.2
                    matched_signals.append(f"Header: '{req_header}'")

            # Normalize confidence score between 0.0 and 1.0
            final_confidence = min(round(score, 2), 1.0)

            if final_confidence > highest_score:
                highest_score = final_confidence
                best_doc_type = rule.doc_type
                best_signals = matched_signals
                best_reason = f"Matched {len(matched_signals)} keyword/header signals."

        return best_doc_type, highest_score, best_signals, best_reason