"""Pydantic data models for the Structured Data Extraction Engine."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.parser.models import ParsedDocument


class HeaderFields(BaseModel):
    """Header information common across structured business documents."""

    document_number: Optional[str] = Field(default=None, description="Invoice, PO, or Voucher number")
    document_date: Optional[str] = Field(default=None, description="Date of document issuance")
    due_date: Optional[str] = Field(default=None, description="Payment due date")
    reference_number: Optional[str] = Field(default=None, description="Associated PO or reference number")
    place_of_supply: Optional[str] = Field(default=None, description="GST place of supply state/code")


class PartyInformation(BaseModel):
    """Vendor, Customer, or B2B Entity details."""

    name: Optional[str] = Field(default=None, description="Entity or individual name")
    gstin: Optional[str] = Field(default=None, description="15-digit GSTIN")
    pan: Optional[str] = Field(default=None, description="10-digit PAN")
    address: Optional[str] = Field(default=None, description="Full physical or billing address")
    email: Optional[str] = Field(default=None, description="Email contact")
    phone: Optional[str] = Field(default=None, description="Phone number")


class LineItem(BaseModel):
    """Itemized product, service, or transaction record."""

    item_number: Optional[int] = Field(default=None, description="Line sequence index")
    description: Optional[str] = Field(default=None, description="Product/Service description or transaction narrative")
    hsn_sac: Optional[str] = Field(default=None, description="HSN or SAC code")
    quantity: Optional[str] = Field(default=None, description="Quantity")
    unit_price: Optional[str] = Field(default=None, description="Unit rate or price")
    amount: Optional[str] = Field(default=None, description="Total line amount")


class TaxInformation(BaseModel):
    """Tax breakdowns extracted from document."""

    cgst: Optional[str] = Field(default=None, description="CGST amount")
    sgst: Optional[str] = Field(default=None, description="SGST amount")
    igst: Optional[str] = Field(default=None, description="IGST amount")
    total_tax: Optional[str] = Field(default=None, description="Total tax amount")


class PaymentInformation(BaseModel):
    """Payment, banking, or settlement details."""

    mode: Optional[str] = Field(default=None, description="Payment mode (Bank Transfer, UPI, Cheque)")
    bank_account: Optional[str] = Field(default=None, description="Bank account number")
    ifsc_code: Optional[str] = Field(default=None, description="Bank IFSC code")
    transaction_id: Optional[str] = Field(default=None, description="Transaction or Cheque reference")


class DocumentTotals(BaseModel):
    """Summary amounts and currency."""

    subtotal: Optional[str] = Field(default=None, description="Taxable amount / subtotal")
    tax_amount: Optional[str] = Field(default=None, description="Aggregate tax amount")
    grand_total: Optional[str] = Field(default=None, description="Final payable amount")
    currency: str = Field(default="INR", description="Currency code (e.g., INR, USD)")


class ExtractionMetadata(BaseModel):
    """Operational metadata regarding the extraction process."""

    document_type: str = Field(..., description="Document classification type")
    extracted_fields_count: int = Field(default=0, description="Count of non-null extracted fields")
    tables_extracted: int = Field(default=0, description="Number of structured tables processed")
    processing_time_ms: float = Field(default=0.0, description="Extraction runtime in ms")


class StructuredBusinessDocument(BaseModel):
    """Normalized structured data container returned for all business documents."""

    document_id: str = Field(..., description="Unique document UUID")
    header: HeaderFields = Field(default_factory=HeaderFields)
    seller: PartyInformation = Field(default_factory=PartyInformation)
    buyer: PartyInformation = Field(default_factory=PartyInformation)
    line_items: List[LineItem] = Field(default_factory=list)
    taxes: TaxInformation = Field(default_factory=TaxInformation)
    payment: PaymentInformation = Field(default_factory=PaymentInformation)
    totals: DocumentTotals = Field(default_factory=DocumentTotals)
    additional_fields: Dict[str, Any] = Field(default_factory=dict)
    metadata: ExtractionMetadata = Field(...)


class ExtractorInput(BaseModel):
    """Input parameters provided to the Extractor Tool."""

    parsed_document: ParsedDocument = Field(..., description="Parsed document payload from Parser Tool")
    document_type: str = Field(..., description="Classification category from Classifier Tool")