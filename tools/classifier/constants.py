"""Constants and document type declarations for the Classification Engine."""

from typing import Set


class DocumentType:
    """Supported business document types."""

    SALES_INVOICE = "Sales Invoice"
    PURCHASE_INVOICE = "Purchase Invoice"
    PURCHASE_ORDER = "Purchase Order"
    QUOTATION = "Quotation"
    SALES_ORDER = "Sales Order"
    CREDIT_NOTE = "Credit Note"
    DEBIT_NOTE = "Debit Note"
    DELIVERY_CHALLAN = "Delivery Challan"
    GOODS_RECEIPT_NOTE = "Goods Receipt Note"
    RECEIPT = "Receipt"
    PAYMENT_VOUCHER = "Payment Voucher"
    EXPENSE_BILL = "Expense Bill"
    BANK_STATEMENT = "Bank Statement"
    GST_INVOICE = "GST Invoice"
    GST_RETURN = "GST Return"
    SALARY_SLIP = "Salary Slip"
    UNKNOWN = "Unknown Document"


ALL_SUPPORTED_DOCUMENT_TYPES: Set[str] = {
    DocumentType.SALES_INVOICE,
    DocumentType.PURCHASE_INVOICE,
    DocumentType.PURCHASE_ORDER,
    DocumentType.QUOTATION,
    DocumentType.SALES_ORDER,
    DocumentType.CREDIT_NOTE,
    DocumentType.DEBIT_NOTE,
    DocumentType.DELIVERY_CHALLAN,
    DocumentType.GOODS_RECEIPT_NOTE,
    DocumentType.RECEIPT,
    DocumentType.PAYMENT_VOUCHER,
    DocumentType.EXPENSE_BILL,
    DocumentType.BANK_STATEMENT,
    DocumentType.GST_INVOICE,
    DocumentType.GST_RETURN,
    DocumentType.SALARY_SLIP,
    DocumentType.UNKNOWN,
}

# Confidence threshold below which a document is categorized as Unknown Document
MINIMUM_CONFIDENCE_THRESHOLD: float = 0.35