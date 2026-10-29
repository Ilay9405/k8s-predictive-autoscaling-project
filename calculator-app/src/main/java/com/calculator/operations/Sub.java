package com.calculator.operations;

import com.calculator.Operation;

public class Sub implements Operation {

    @Override
    public double calculate(double a, double b) {
        return a - b;
    }
}
