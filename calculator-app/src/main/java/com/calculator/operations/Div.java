package com.calculator.operations;

import com.calculator.Operation;

public class Div implements Operation {

    @Override
    public double calculate(double a, double b) {
        if (b == 0) {
            throw new IllegalArgumentException("cant divide by zero");
        }
        return a / b;
    }
}
