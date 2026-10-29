package com.calculator;

public class App {

    public static void main(String[] args) {
        Calculator calc = new Calculator();

        System.out.println("=== Calculator ===");
        System.out.println("10 + 5 = " + (int) calc.calculate("+", 10, 5));
        System.out.println("10 - 5 = " + (int) calc.calculate("-", 10, 5));
        System.out.println("10 * 5 = " + (int) calc.calculate("*", 10, 5));
        System.out.println("10 / 5 = " + (int) calc.calculate("/", 10, 5));
        System.out.println("==================");
    }
}
