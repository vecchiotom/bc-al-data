codeunit 50000 "BAD Hello World"
{
    trigger OnRun()
    var
        Cust: Record Customer;
    begin
        if Cust.FindSet() then
            Message('Customers: %1', Cust.Count());
    end;
}
