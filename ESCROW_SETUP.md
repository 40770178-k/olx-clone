# Escrow Payment Setup

The marketplace includes an escrow payment option. Funds are **authorized** when the buyer pays, but **not captured** until the buyer confirms receipt. This protects both parties.

## Flow

1. **Buyer** clicks "Pay with Escrow" on an item or in a conversation
2. Buyer is redirected to **Stripe Checkout** to enter card details
3. Payment is **authorized** (funds held, not captured)
4. **Seller** optionally marks item as "Shipped"
5. **Buyer** confirms "I Received It" → funds are **captured** and released to the platform
6. Or **Buyer** opens a dispute → authorization is cancelled, buyer is refunded

## Stripe Configuration

1. Create a [Stripe account](https://dashboard.stripe.com/register)
2. Get your API keys from [Stripe Dashboard → Developers → API keys](https://dashboard.stripe.com/apikeys)
3. Set environment variables:

```bash
# Windows PowerShell
$env:STRIPE_SECRET_KEY = "sk_test_..."
$env:STRIPE_PUBLISHABLE_KEY = "pk_test_..."

# Linux/Mac
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_PUBLISHABLE_KEY="pk_test_..."
```

4. Install dependencies: `pip install stripe`

## Without Stripe (Demo Mode)

If Stripe keys are not set, escrow transactions can still be created in "demo mode". The flow is tracked in the database but no real payments occur. Useful for development and testing.

## Seller Payouts

Currently, when the buyer confirms receipt, funds are **captured** to your Stripe account. To pay out sellers automatically, you would need to add [Stripe Connect](https://stripe.com/docs/connect) and have sellers connect their Stripe accounts.
