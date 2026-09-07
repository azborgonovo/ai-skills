using Xunit;

namespace Billing.Tests;

public class InvoiceTests
{
    [Fact]
    [Trait("covers", "SCN-0201")]
    public void An_invoice_totals_the_lines_it_holds()
    {
        var invoice = new Invoice(new DateOnly(2026, 1, 10));
        invoice.AddLine("Support", 200m);
        invoice.AddLine("Hosting", 50m);

        Assert.Equal(250m, invoice.Total);
    }

    [Fact]
    [Trait("covers", "SCN-0202")]
    public void A_credit_note_reduces_the_invoice_total()
    {
        var invoice = new Invoice(new DateOnly(2026, 1, 10));
        invoice.AddLine("Support", 200m);
        invoice.AddCreditNote(50m);

        Assert.Equal(150m, invoice.Total);
    }

    [Fact]
    [Trait("covers", "SCN-0299")]
    public void An_invoice_with_no_lines_totals_zero()
    {
        var invoice = new Invoice(new DateOnly(2026, 1, 10));

        Assert.Equal(0m, invoice.Total);
    }
}
