package com.calculator;

import com.calculator.operations.Add;
import com.calculator.operations.Sub;
import com.calculator.operations.Mul;
import com.calculator.operations.Div;

public class Calculator {

    private final Operation add = new Add();
    private final Operation sub = new Sub();
    private final Operation mul = new Mul();
    private final Operation div = new Div();

    public double calculate(String symbol, double a, double b) {
        switch (symbol) {
            case "+":
                return add.calculate(a, b);
            case "-":
                return sub.calculate(a, b);
            case "*":
                return mul.calculate(a, b);
            case "/":
                return div.calculate(a, b);

            default:
                throw new IllegalArgumentException("Unknown operation symbol: " + symbol);
        }
    }
}
