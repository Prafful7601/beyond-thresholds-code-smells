package demo;

public class Pricing {
    public int base(int qty) {
        return qty * 10;
    }

    public double tax(double amount, String region, boolean exempt, int year, String currency) {
        if (exempt) {
            return 0;
        }
        if (region.equals("EU")) {
            return amount * 0.21;
        }
        if (year > 2025) {
            return amount * 0.19;
        }
        return amount * 0.2;
    }

    public String label(String name) {
        return "[" + name + "]";
    }

    public int discount(int qty, int loyalty) {
        int d = 0;
        for (int i = 0; i < qty; i++) {
            if (i % 10 == 0) {
                d++;
            }
        }
        while (d > loyalty) {
            d--;
        }
        return d > 5 ? 5 : d;
    }
}
