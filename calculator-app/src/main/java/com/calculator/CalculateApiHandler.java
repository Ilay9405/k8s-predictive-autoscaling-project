package com.calculator;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

public class CalculateApiHandler implements HttpHandler {

    private final Calculator calculator;

    public CalculateApiHandler(Calculator calculator) {
        this.calculator = calculator;
    }

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
        Map<String, String> params = parseForm(body);

        String html;
        try {
            double a = Double.parseDouble(params.getOrDefault("a", ""));
            String op = params.getOrDefault("op", "").trim();
            double b = Double.parseDouble(params.getOrDefault("b", ""));
            double result = calculator.calculate(op, a, b);
            html = "<html><body><h2>Result: " + a + " " + op + " " + b + " = " + result + "</h2>" +
                   "<a href=\"/\">Go back</a></body></html>";
        } catch (Exception e) {
            html = "<html><body><h2>Error: " + e.getMessage() + "</h2>" +
                   "<a href=\"/\">Go back</a></body></html>";
        }

        byte[] bytes = html.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
        exchange.sendResponseHeaders(200, bytes.length);
        OutputStream os = exchange.getResponseBody();
        os.write(bytes);
        os.close();
    }

    private Map<String, String> parseForm(String body) {
        Map<String, String> result = new HashMap<>();
        for (String pair : body.split("&")) {
            String[] kv = pair.split("=", 2);
            if (kv.length == 2) {
                result.put(
                        URLDecoder.decode(kv[0], StandardCharsets.UTF_8),
                        URLDecoder.decode(kv[1], StandardCharsets.UTF_8));
            }
        }
        return result;
    }
}
