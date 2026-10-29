package com.calculator;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

public class UiHandler implements HttpHandler {

    private static final String HTML =
        "<html><body>" +
        "<h2>Calculator</h2>" +
        "<form method=\"POST\" action=\"/calculate\">" +
        "  <input type=\"number\" name=\"a\" placeholder=\"First number\" step=\"any\" /><br/><br/>" +
        "  <select name=\"op\">" +
        "    <option>+</option>" +
        "    <option>-</option>" +
        "    <option>*</option>" +
        "    <option>/</option>" +
        "  </select><br/><br/>" +
        "  <input type=\"number\" name=\"b\" placeholder=\"Second number\" step=\"any\" /><br/><br/>" +
        "  <button type=\"submit\">Calculate</button>" +
        "</form>" +
        "</body></html>";

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        byte[] bytes = HTML.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "text/html; charset=utf-8");
        exchange.sendResponseHeaders(200, bytes.length);
        OutputStream os = exchange.getResponseBody();
        os.write(bytes);
        os.close();
    }
}
