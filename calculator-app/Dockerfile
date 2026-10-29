# Stage I: Build Stage
FROM maven:3.9-eclipse-temurin-25 AS builder
WORKDIR /app
COPY . .
RUN mvn clean package -DskipTests

# Stage II: Execution Stage
FROM eclipse-temurin:25-jre
WORKDIR /app
COPY --from=builder /app/target/calculator-app-1.0-SNAPSHOT.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]