"""Deterministic Financial Analytics API Router."""

import re
from typing import Dict, List, Optional, Set, Tuple
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from logger import logger
from tools.vector_retrieval.constants import (
    DEFAULT_COLLECTION_NAME,
    META_KEY_CHUNK_INDEX,
    META_KEY_DOCUMENT_ID,
    META_KEY_WORKSPACE_ID,
)
from tools.vector_retrieval.service import VectorRetrievalService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class FinancialSummaryResponse(BaseModel):
    """Deterministic financial summary aggregated across requested documents."""

    workspace_id: str = Field(..., description="Target workspace identifier")
    document_ids: List[str] = Field(..., description="List of analyzed document UUIDs")
    total_credit_amount: Optional[float] = Field(default=None, description="Sum of credit transactions")
    total_debit_amount: Optional[float] = Field(default=None, description="Sum of debit transactions")
    net_cash_flow: Optional[float] = Field(default=None, description="Calculated total_credits - total_debits")
    total_transactions: int = Field(default=0, description="Total count of transactions across statements")
    opening_balance: Optional[float] = Field(default=None, description="Opening balance of first analyzed statement")
    closing_balance: Optional[float] = Field(default=None, description="Closing balance of last analyzed statement")
    invoice_subtotal: Optional[float] = Field(default=None, description="Sum of invoice subtotals")
    invoice_tax: Optional[float] = Field(default=None, description="Sum of invoice taxes")
    invoice_grand_total: Optional[float] = Field(default=None, description="Sum of invoice grand totals")
    currency: str = Field(default="INR", description="Dominant or default currency code")
    documents_analyzed: int = Field(default=0, description="Number of valid scoped documents analyzed")


class TransactionItem(BaseModel):
    """Normalized transaction row derived deterministically from stored document data."""

    item_number: int = Field(..., description="Sequence number")
    date: Optional[str] = Field(default=None, description="Transaction date if present")
    description: Optional[str] = Field(default=None, description="Transaction narrative/description")
    transaction_type: Optional[str] = Field(default=None, description="Credit or Debit indicator (CR/DB)")
    amount: Optional[float] = Field(default=None, description="Parsed numeric amount")
    credit_amount: Optional[float] = Field(default=None, description="Credit amount if applicable")
    debit_amount: Optional[float] = Field(default=None, description="Debit amount if applicable")
    balance: Optional[float] = Field(default=None, description="Running balance if present")
    raw_text: str = Field(..., description="Original raw line item representation")


class TransactionListResponse(BaseModel):
    """Paginated list of normalized transaction records."""

    workspace_id: str = Field(..., description="Target workspace identifier")
    document_id: str = Field(..., description="Analyzed document UUID")
    total_transactions: int = Field(..., description="Total transactions available for this document")
    limit: int = Field(..., description="Pagination limit")
    offset: int = Field(..., description="Pagination offset")
    transactions: List[TransactionItem] = Field(default_factory=list, description="List of transaction records")


def _parse_float(val: Optional[str]) -> Optional[float]:
    """Safely extracts a float from a string."""
    if not val or not str(val).strip():
        return None
    cleaned = re.sub(r"[^\d.-]", "", str(val).strip().replace(",", ""))
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


@router.get(
    "/summary",
    response_model=FinancialSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get deterministic financial and invoice summary metrics across scoped documents",
)
async def get_financial_summary(
    workspace_id: str = Query(..., min_length=1, description="Target workspace ID"),
    document_ids: List[str] = Query(..., min_length=1, description="List of document IDs to aggregate"),
) -> FinancialSummaryResponse:
    """Aggregates authoritative financial metrics from stored Chunk 0 records without LLM calls."""
    clean_workspace_id = workspace_id.strip()
    valid_doc_ids = [d.strip() for d in document_ids if d.strip()]

    if not clean_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workspace_id cannot be empty.",
        )

    if not valid_doc_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_ids list cannot be empty.",
        )

    try:
        retrieval_svc = VectorRetrievalService()
        client = retrieval_svc._get_client()

        try:
            collection = client.get_collection(name=DEFAULT_COLLECTION_NAME)
        except Exception:
            return FinancialSummaryResponse(
                workspace_id=clean_workspace_id,
                document_ids=valid_doc_ids,
                documents_analyzed=0,
            )

        total_credits = 0.0
        total_debits = 0.0
        has_credits = False
        has_debits = False
        total_txns = 0
        first_open_bal: Optional[float] = None
        last_close_bal: Optional[float] = None

        inv_subtotal = 0.0
        inv_tax = 0.0
        inv_grand_total = 0.0
        has_inv_subtotal = False
        has_inv_tax = False
        has_inv_grand_total = False
        currency = "INR"
        analyzed_count = 0

        for doc_id in valid_doc_ids:
            records = collection.get(
                where={
                    "$and": [
                        {META_KEY_WORKSPACE_ID: {"$eq": clean_workspace_id}},
                        {META_KEY_DOCUMENT_ID: {"$eq": doc_id}},
                    ]
                },
                include=["documents", "metadatas"],
            )

            s_ids = records.get("ids") or []
            s_docs = records.get("documents") or []
            s_metas = records.get("metadatas") or []

            for s_idx, s_meta in enumerate(s_metas):
                if not isinstance(s_meta, dict):
                    continue

                try:
                    chunk_idx = int(s_meta.get(META_KEY_CHUNK_INDEX, -1))
                except (TypeError, ValueError):
                    continue

                if chunk_idx == 0:
                    analyzed_count += 1
                    text_chunk = s_docs[s_idx] if s_idx < len(s_docs) and s_docs[s_idx] else ""

                    # Parse Statement Totals
                    cr_match = re.search(r"Total Credit Amount:\s*([^\n\r]+)", text_chunk, re.IGNORECASE)
                    if cr_match:
                        val = _parse_float(cr_match.group(1))
                        if val is not None:
                            total_credits += val
                            has_credits = True

                    dr_match = re.search(r"Total Debit Amount:\s*([^\n\r]+)", text_chunk, re.IGNORECASE)
                    if dr_match:
                        val = _parse_float(dr_match.group(1))
                        if val is not None:
                            total_debits += val
                            has_debits = True

                    txn_match = re.search(r"Total Transactions:\s*([^\n\r]+)", text_chunk, re.IGNORECASE)
                    if txn_match:
                        val = _parse_float(txn_match.group(1))
                        if val is not None:
                            total_txns += int(val)

                    op_match = re.search(r"Opening Balance:\s*([^\n\r]+)", text_chunk, re.IGNORECASE)
                    if op_match:
                        val = _parse_float(op_match.group(1))
                        if val is not None and first_open_bal is None:
                            first_open_bal = val

                    cl_match = re.search(r"Closing Balance:\s*([^\n\r]+)", text_chunk, re.IGNORECASE)
                    if cl_match:
                        val = _parse_float(cl_match.group(1))
                        if val is not None:
                            last_close_bal = val

                    # Parse Invoice Totals
                    sub_match = re.search(r"Subtotal:\s*([^\n\r]+)", text_chunk, re.IGNORECASE)
                    if sub_match:
                        val = _parse_float(sub_match.group(1))
                        if val is not None:
                            inv_subtotal += val
                            has_inv_subtotal = True

                    tax_match = re.search(r"Tax Amount:\s*([^\n\r]+)", text_chunk, re.IGNORECASE)
                    if tax_match:
                        val = _parse_float(tax_match.group(1))
                        if val is not None:
                            inv_tax += val
                            has_inv_tax = True

                    gt_match = re.search(r"Grand Total:\s*([^\n\r]+)", text_chunk, re.IGNORECASE)
                    if gt_match:
                        val = _parse_float(gt_match.group(1))
                        if val is not None:
                            inv_grand_total += val
                            has_inv_grand_total = True

                    curr_match = re.search(r"Currency:\s*([A-Za-z]+)", text_chunk, re.IGNORECASE)
                    if curr_match:
                        currency = curr_match.group(1).upper()

                    break

        net_cash_flow = None
        if has_credits or has_debits:
            net_cash_flow = round(total_credits - total_debits, 2)

        return FinancialSummaryResponse(
            workspace_id=clean_workspace_id,
            document_ids=valid_doc_ids,
            total_credit_amount=round(total_credits, 2) if has_credits else None,
            total_debit_amount=round(total_debits, 2) if has_debits else None,
            net_cash_flow=net_cash_flow,
            total_transactions=total_txns,
            opening_balance=first_open_bal,
            closing_balance=last_close_bal,
            invoice_subtotal=round(inv_subtotal, 2) if has_inv_subtotal else None,
            invoice_tax=round(inv_tax, 2) if has_inv_tax else None,
            invoice_grand_total=round(inv_grand_total, 2) if has_inv_grand_total else None,
            currency=currency,
            documents_analyzed=analyzed_count,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to generate financial summary: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating financial summary.",
        )


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get paginated normalized transactions for a specific document without chunk overlap duplicates",
)
async def get_document_transactions(
    workspace_id: str = Query(..., min_length=1, description="Target workspace ID"),
    document_id: str = Query(..., min_length=1, description="Target document ID"),
    limit: int = Query(default=100, ge=1, le=500, description="Pagination limit"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
) -> TransactionListResponse:
    """Extracts, deduplicates across overlapping chunks, and paginates structured transaction line items."""
    clean_workspace_id = workspace_id.strip()
    clean_doc_id = document_id.strip()

    if not clean_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workspace_id cannot be empty.",
        )

    if not clean_doc_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="document_id cannot be empty.",
        )

    try:
        retrieval_svc = VectorRetrievalService()
        client = retrieval_svc._get_client()

        try:
            collection = client.get_collection(name=DEFAULT_COLLECTION_NAME)
        except Exception:
            return TransactionListResponse(
                workspace_id=clean_workspace_id,
                document_id=clean_doc_id,
                total_transactions=0,
                limit=limit,
                offset=offset,
                transactions=[],
            )

        records = collection.get(
            where={
                "$and": [
                    {META_KEY_WORKSPACE_ID: {"$eq": clean_workspace_id}},
                    {META_KEY_DOCUMENT_ID: {"$eq": clean_doc_id}},
                ]
            },
            include=["documents", "metadatas"],
        )

        s_ids = records.get("ids") or []
        s_docs = records.get("documents") or []
        s_metas = records.get("metadatas") or []

        if not s_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{clean_doc_id}' not found in workspace '{clean_workspace_id}'.",
            )

        # Sort chunks strictly by chunk_index
        indexed_chunks: List[Tuple[int, str]] = []
        for idx, meta in enumerate(s_metas):
            if isinstance(meta, dict):
                c_idx = int(meta.get(META_KEY_CHUNK_INDEX, 0))
                doc_text = s_docs[idx] if idx < len(s_docs) else ""
                indexed_chunks.append((c_idx, doc_text))

        indexed_chunks.sort(key=lambda x: x[0])

        all_transactions: List[TransactionItem] = []
        seen_item_keys: Set[Tuple[int, Optional[str], Optional[float]]] = set()
        seen_item_numbers: Set[int] = set()

        # Parse line items across chunks, ignoring duplicates introduced by chunk overlap
        for _, text_chunk in indexed_chunks:
            lines = text_chunk.split("\n")
            for line in lines:
                line_clean = line.strip()

                # Match strict line item header: Item <num>: <content>
                item_header_match = re.match(r"^Item\s+(\d+)\s*:\s*(.+)$", line_clean, re.IGNORECASE)
                if not item_header_match:
                    continue

                item_num = int(item_header_match.group(1))
                item_body = item_header_match.group(2).strip()

                # Extract Date
                date_match = re.search(r"Date:\s*([\d\-/]+)", item_body, re.IGNORECASE)
                date_val = date_match.group(1).strip() if date_match else None

                # Extract Direction Type
                type_match = re.search(r"Type:\s*([A-Za-z]+)", item_body, re.IGNORECASE)
                type_val = type_match.group(1).upper() if type_match else None

                # Extract Amount
                amt_match = re.search(r"Amount:\s*([\d\.,-]+)", item_body, re.IGNORECASE)
                amt_val = _parse_float(amt_match.group(1)) if amt_match else None

                # Deduplication check: Item numbers are deterministic 1-based sequence numbers
                dedup_key = (item_num, date_val, amt_val)
                if item_num in seen_item_numbers or dedup_key in seen_item_keys:
                    continue

                # Extract Balance
                bal_match = re.search(r"Balance:\s*([\d\.,-]+)", item_body, re.IGNORECASE)
                bal_val = _parse_float(bal_match.group(1)) if bal_match else None

                # Determine Credit vs Debit
                cr_amt = None
                dr_amt = None
                if type_val in ["CR", "CREDIT"]:
                    cr_amt = amt_val
                elif type_val in ["DR", "DB", "DEBIT"]:
                    dr_amt = amt_val

                # Extract Description / Narrative
                desc_match = re.search(r"Description:\s*([^|]+)", item_body, re.IGNORECASE)
                if desc_match:
                    desc_val = desc_match.group(1).strip()
                else:
                    parts = [p.strip() for p in item_body.split("|") if p.strip()]
                    non_key_parts = [
                        p for p in parts
                        if not any(p.lower().startswith(k) for k in ["date:", "type:", "amount:", "balance:", "mode:", "qty:", "unit price:", "total:"])
                    ]
                    desc_val = " | ".join(non_key_parts) if non_key_parts else item_body

                transaction_record = TransactionItem(
                    item_number=item_num,
                    date=date_val,
                    description=desc_val,
                    transaction_type=type_val,
                    amount=amt_val,
                    credit_amount=cr_amt,
                    debit_amount=dr_amt,
                    balance=bal_val,
                    raw_text=line_clean,
                )

                all_transactions.append(transaction_record)
                seen_item_numbers.add(item_num)
                seen_item_keys.add(dedup_key)

        # Sort transactions in stable item_number order
        all_transactions.sort(key=lambda t: t.item_number)
        paginated = all_transactions[offset : offset + limit]

        return TransactionListResponse(
            workspace_id=clean_workspace_id,
            document_id=clean_doc_id,
            total_transactions=len(all_transactions),
            limit=limit,
            offset=offset,
            transactions=paginated,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to retrieve transactions: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving transaction details.",
        )
