package com.calculator.operations;

import com.calculator.Operation;

public class Add implements Operation {

    @Override
    public double calculate(double a, double b) {
        return a + b;
    }
}
