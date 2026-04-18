package com.example.chat

import org.springframework.boot.test.context.SpringBootTest
import org.springframework.test.context.DynamicPropertyRegistry
import org.springframework.test.context.DynamicPropertySource
import org.testcontainers.containers.PostgreSQLContainer
import org.testcontainers.junit.jupiter.Testcontainers

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
abstract class AbstractIntegrationTest {

    companion object {
        // Single shared container for the entire test suite — started once, reused across all test classes.
        // Flyway migrations run automatically on first connection.
        val postgres: PostgreSQLContainer<*> = PostgreSQLContainer("postgres:16-alpine")
            .withDatabaseName("chat_test")
            .withUsername("chat")
            .withPassword("chat")
            .apply { start() }

        @JvmStatic
        @DynamicPropertySource
        fun properties(registry: DynamicPropertyRegistry) {
            registry.add("spring.datasource.url", postgres::getJdbcUrl)
            registry.add("spring.datasource.username", postgres::getUsername)
            registry.add("spring.datasource.password", postgres::getPassword)
        }
    }

    // Subclasses must clean up their own data in @AfterEach.
    // Do NOT use @Transactional rollback — it does not work in RANDOM_PORT tests:
    // the server runs on a separate thread; transactions commit before the test client
    // receives the response. Use explicit deleteAll() calls instead.
    //
    // Example:
    // @AfterEach
    // fun cleanup() {
    //     messageRepository.deleteAll()
    //     roomRepository.deleteAll()
    //     userRepository.deleteAll()
    // }
}
