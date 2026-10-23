package demo;

public class Pricing {
    public int base(int qty) {
        return qty * 10;
    }

    public double tax(double amount) {
        return amount * 0.2;
    }

    public void legacy(int a) {
        System.out.println(a);
    }

    public String label(String name) {
        return "[" + name + "]";
    }
}
