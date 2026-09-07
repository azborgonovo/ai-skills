namespace Billing;

public record InvoiceLine(string Description, decimal Amount);

public class Invoice
{
    private readonly List<InvoiceLine> _lines = new();

    public Invoice(DateOnly issuedOn) => IssuedOn = issuedOn;

    public DateOnly IssuedOn { get; }

    public decimal Total => _lines.Sum(line => line.Amount);

    public void AddLine(string description, decimal amount)
        => _lines.Add(new InvoiceLine(description, amount));

    public void AddCreditNote(decimal amount)
        => _lines.Add(new InvoiceLine("Credit note", -amount));
}
