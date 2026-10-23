package demo;

import java.util.List;

/** Small hand-written example with methods in every zone. */
public class OrderService {

    // clean for both smells: cc 1, pc 1
    public int count(List<String> items) {
        return items.size();
    }

    // borderline Complex Method: cc 6 (5 decisions), pc 2
    public double discount(double total, int loyaltyYears) {
        double rate = 0.0;
        if (total > 100) {
            rate += 0.05;
        }
        if (loyaltyYears > 2) {
            rate += 0.02;
        }
        for (int i = 0; i < loyaltyYears; i++) {
            rate += 0.001;
        }
        while (rate > 0.2) {
            rate -= 0.01;
        }
        return total > 1000 ? rate + 0.01 : rate;
    }

    // borderline Long Parameter List: pc 5
    public String label(String name, String street, String city, String zip, String country) {
        return name + ", " + street + ", " + city + " " + zip + ", " + country;
    }

    // clear Complex Method: cc 16 (15 decisions)
    public int grade(int a, int b) {
        int g = 0;
        if (a > 1) { g++; }
        if (a > 2) { g++; }
        if (a > 3) { g++; }
        if (a > 4) { g++; }
        if (a > 5) { g++; }
        if (b > 1) { g++; }
        if (b > 2) { g++; }
        if (b > 3) { g++; }
        if (b > 4) { g++; }
        if (b > 5) { g++; }
        for (int i = 0; i < a; i++) { g++; }
        for (int j = 0; j < b; j++) { g++; }
        while (g > 100) { g--; }
        while (g < -100) { g++; }
        return g > 10 ? 10 : g;
    }
}
