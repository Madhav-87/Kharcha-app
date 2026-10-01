"""UPI intent generation helpers."""

from urllib.parse import urlencode


def build_upi_intent(payment):
    """Build an intent URI; it is a handoff request, not a payment result."""
    amount = f"{payment.amount_paise // 100}.{payment.amount_paise % 100:02d}"
    parameters = {
        "pa": payment.payee_upi_id,
        "pn": payment.payee_name,
        "am": amount,
        "cu": payment.currency,
        "tr": payment.reference_code,
    }
    if payment.note:
        parameters["tn"] = payment.note
    return f"upi://pay?{urlencode(parameters)}"
