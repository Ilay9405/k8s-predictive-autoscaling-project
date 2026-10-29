package com.calculator;

import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.io.IOException;

public class App {

    public static void main(String[] args) throws IOException {
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        Calculator calc = new Calculator();

        // Serve the terminal-style calculator UI
        server.createContext("/", new UiHandler());
        // REST endpoint: POST /calculate  body: a=<n>&op=<+>&b=<n>
        server.createContext("/calculate", new CalculateApiHandler(calc));
        // Health probe for Kubernetes liveness/readiness checks
        server.createContext("/health", exchange -> {
            byte[] resp = "OK".getBytes();
            exchange.sendResponseHeaders(200, resp.length);
            exchange.getResponseBody().write(resp);
            exchange.getResponseBody().close();
        });

        server.setExecutor(null);
        server.start();
        System.out.printf("Calculator HTTP server listening on :%d%n", port);
    }
}
