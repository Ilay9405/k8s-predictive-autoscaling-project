package com.calculator;

import org.junit.jupiter.api.BeforeEach; // Reccomended package for java testing
import org.junit.jupiter.api.Test; // Reccomended package for java testing

import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {

    private Calculator calculator;

    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }

    @Test
    void testAddition() {
        double result = calculator.calculate("+", 5.0, 3.0);
        assertEquals(8.0, result, 0.0001);
    }

    @Test
    void testSubtraction() {
        double result = calculator.calculate("-", 10.0, 4.0);
        assertEquals(6.0, result, 0.0001);
    }

    @Test
    void testMultiplication() {
        double result = calculator.calculate("*", 3.0, 7.0);
        assertEquals(21.0, result, 0.0001);
    }

    @Test
    void testDivision() {
        double result = calculator.calculate("/", 20.0, 4.0);
        assertEquals(5.0, result, 0.0001);
    }

    @Test
    void testUnknownOperationThrowsException() {
        Exception exception = assertThrows(IllegalArgumentException.class, () -> {
            calculator.calculate("%", 5.0, 2.0);
        });

        assertTrue(exception.getMessage().contains("Unknown operation symbol: %"));
    }
}