"""
Escrow payment service using Stripe.
Uses PaymentIntent with manual capture: authorize on payment, capture when buyer confirms receipt.
"""
import stripe
from django.conf import settings
from django.urls import reverse


def is_stripe_configured():
    """Check if Stripe is properly configured."""
    return bool(settings.STRIPE_SECRET_KEY)


def create_escrow_checkout_session(escrow, request):
    """
    Create a Stripe Checkout Session for escrow payment.
    Uses manual capture - funds are authorized but not captured until buyer confirms receipt.
    """
    if not is_stripe_configured():
        return None, "Stripe is not configured. Set STRIPE_SECRET_KEY in your environment."

    stripe.api_key = settings.STRIPE_SECRET_KEY

    success_url = request.build_absolute_uri(
        reverse('escrow-success', kwargs={'pk': escrow.pk})
    ) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(
        reverse('escrow-detail', kwargs={'pk': escrow.pk})
    )

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': escrow.item.title,
                        'description': f'Escrow payment for {escrow.item.title}. Funds held until you confirm receipt.',
                        'images': [request.build_absolute_uri(escrow.item.image.url)] if escrow.item.image else [],
                    },
                    'unit_amount': int(escrow.amount * 100),  # Stripe uses cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=str(escrow.pk),
            metadata={
                'escrow_id': str(escrow.pk),
                'item_id': str(escrow.item_id),
                'buyer_id': str(escrow.buyer_id),
                'seller_id': str(escrow.seller_id),
            },
            payment_intent_data={
                'capture_method': 'manual',  # Escrow: authorize now, capture when buyer confirms
                'metadata': {
                    'escrow_id': str(escrow.pk),
                },
            },
        )
        return session, None
    except stripe.error.StripeError as e:
        return None, str(e)


def capture_escrow_payment(escrow):
    """
    Capture the authorized payment when buyer confirms receipt.
    Releases funds to the platform (seller payout would use Stripe Connect).
    """
    if not escrow.stripe_payment_intent_id:
        return False, "No payment intent associated with this escrow."

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        intent = stripe.PaymentIntent.capture(escrow.stripe_payment_intent_id)
        return intent.status == 'succeeded', None
    except stripe.error.StripeError as e:
        return False, str(e)


def cancel_escrow_payment(escrow):
    """Cancel the authorization and release the hold (for refunds/disputes)."""
    if not escrow.stripe_payment_intent_id:
        return False, "No payment intent associated with this escrow."

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        stripe.PaymentIntent.cancel(escrow.stripe_payment_intent_id)
        return True, None
    except stripe.error.StripeError as e:
        return False, str(e)


def get_payment_intent_from_session(session_id):
    """Retrieve PaymentIntent ID from a Checkout Session."""
    if not is_stripe_configured():
        return None

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        pi = session.payment_intent
        return pi if isinstance(pi, str) else (pi.id if pi else None)
    except stripe.error.StripeError:
        return None
