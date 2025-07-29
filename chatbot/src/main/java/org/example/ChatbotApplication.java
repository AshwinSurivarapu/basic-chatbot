package org.example;

import org.example.Message;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.*;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.Collections; // For unmodifiable list

@SpringBootApplication
@RestController
@CrossOrigin(origins = "http://localhost:3000") // Allow React app to access
public class ChatbotApplication {

    private final RestTemplate restTemplate = new RestTemplate();
    private final String pythonAiServiceUrl = "http://localhost:5001/chat"; // Python service URL

    // In-memory list to store conversation history
    // Volatile for basic thread safety if multiple requests hit concurrently, though not strictly needed for single-user demo
    private final List<Message> conversationHistory = Collections.synchronizedList(new ArrayList<>());
    private final int MAX_HISTORY_SIZE = 20; // Keep last 20 messages (10 user, 10 AI)

    public static void main(String[] args) {
        SpringApplication.run(ChatbotApplication.class, args);
    }

    @PostMapping("/api/message")
    public ResponseEntity<Map<String, String>> handleMessage(@RequestBody Map<String, String> payload) {
        String userMessageText = payload.get("message");
        if (userMessageText == null || userMessageText.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("response", "Message cannot be empty."));
        }

        // Add user message to history
        addMessageToHistory(new Message("user", userMessageText));

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            Map<String, String> pythonRequest = new HashMap<>();
            pythonRequest.put("message", userMessageText); // Only sending current message to AI

            HttpEntity<Map<String, String>> requestEntity = new HttpEntity<>(pythonRequest, headers);

            // Forward request to Python AI service
            ResponseEntity<Map> pythonResponse = restTemplate.postForEntity(
                    pythonAiServiceUrl, requestEntity, Map.class);

            String aiResponseText = (String) pythonResponse.getBody().get("response");

            // Add AI response to history
            addMessageToHistory(new Message("ai", aiResponseText));

            return ResponseEntity.ok(Map.of("response", aiResponseText));

        } catch (Exception e) {
            e.printStackTrace();
            String errorResponse = "Error connecting to AI service.";
            // Add error message to history
            addMessageToHistory(new Message("error", errorResponse));
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("response", errorResponse));
        }
    }

    // New endpoint to retrieve full conversation history
    @GetMapping("/api/history")
    public ResponseEntity<List<Message>> getConversationHistory() {
        // Return an unmodifiable list to prevent external modification
        return ResponseEntity.ok(Collections.unmodifiableList(conversationHistory));
    }

    private void addMessageToHistory(Message message) {
        synchronized (conversationHistory) { // Synchronize access to the shared list
            conversationHistory.add(message);
            // Keep history size limited
            if (conversationHistory.size() > MAX_HISTORY_SIZE) {
                conversationHistory.remove(0); // Remove the oldest message
            }
        }
    }
}