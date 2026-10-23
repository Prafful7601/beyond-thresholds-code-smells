package demo;

/** Interface with a bodiless declaration: clear Long Parameter List (pc 11). */
public interface Shipping {
    double quote(String from, String to, double weight, double width, double height, double depth,
                 boolean express, boolean insured, String carrier, String currency, int days);

    // borderline-free: pc 0
    String name();
}
