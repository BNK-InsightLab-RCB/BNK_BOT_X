package org.bnkbotxapi.bnkbotxapi.engine;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.log4j.Log4j2;
import org.bnkbotxapi.bnkbotxapi.common.exception.CommonExceptions;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
@Log4j2
public class ChatbotEngineClient {

    private final String baseUrl;
    private final ObjectMapper objectMapper;
    private final HttpClient httpClient = HttpClient.newHttpClient();

    public ChatbotEngineClient(EngineProperties properties, ObjectMapper objectMapper) {
        this.baseUrl = properties.getBaseUrl();
        this.objectMapper = objectMapper;
    }

    public EngineQueryResponse query(String question, String role, int topK) {
        try {
            return sendJson("POST", "/query", Map.of("question", question, "role", role, "top_k", topK),
                    EngineQueryResponse.class);
        } catch (Exception e) {
            log.error("engine query failed", e);
            throw CommonExceptions.ENGINE_ERROR.get();
        }
    }

    public Map<String, Object> health() {
        return sendNoBody("GET", "/health", Map.class);
    }

    public Map<String, Object> ingest() {
        return sendNoBody("POST", "/admin/ingest", Map.class);
    }

    public Map<String, Object> handoffs(String status) {
        String uri = status == null || status.isBlank()
                ? "/admin/handoffs"
                : "/admin/handoffs?status=" + encode(status);
        return sendNoBody("GET", uri, Map.class);
    }

    public Map<String, Object> resolveHandoff(Long handoffId) {
        return sendNoBody("POST", "/admin/handoffs/" + handoffId + "/resolve", Map.class);
    }

    public EngineManualListResponse manuals() {
        return sendNoBody("GET", "/admin/manuals", EngineManualListResponse.class);
    }

    public EngineManualDetailDTO manual(String manualId) {
        return sendNoBody("GET", "/admin/manuals/" + encode(manualId), EngineManualDetailDTO.class);
    }

    public Map<String, Object> editManual(String manualId, EngineManualEditRequest request) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("branch_md", request.getBranchMd());
        body.put("it_md", request.getItMd());
        body.put("by", request.getBy());
        return sendJson("PUT", "/admin/manuals/" + encode(manualId), body, Map.class);
    }

    public Map<String, Object> approveManual(String manualId, String by) {
        return sendNoBody("POST", "/admin/manuals/" + encode(manualId) + "/approve?by=" + encode(by), Map.class);
    }

    private <T> T sendNoBody(String method, String path, Class<T> responseType) {
        try {
            HttpRequest request = HttpRequest.newBuilder(uri(path))
                    .version(HttpClient.Version.HTTP_1_1)
                    .header("Accept", "application/json")
                    .method(method, HttpRequest.BodyPublishers.noBody())
                    .build();
            return send(request, responseType);
        } catch (Exception e) {
            log.error("engine request failed", e);
            throw CommonExceptions.ENGINE_ERROR.get();
        }
    }

    private <T> T sendJson(String method, String path, Object body, Class<T> responseType) {
        try {
            String json = objectMapper.writeValueAsString(body);
            HttpRequest request = HttpRequest.newBuilder(uri(path))
                    .version(HttpClient.Version.HTTP_1_1)
                    .header("Accept", "application/json")
                    .header("Content-Type", "application/json")
                    .method(method, HttpRequest.BodyPublishers.ofString(json, StandardCharsets.UTF_8))
                    .build();
            return send(request, responseType);
        } catch (Exception e) {
            log.error("engine request failed", e);
            throw CommonExceptions.ENGINE_ERROR.get();
        }
    }

    private <T> T send(HttpRequest request, Class<T> responseType) throws Exception {
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        if (response.statusCode() >= 400) {
            throw new IllegalStateException("Engine returned " + response.statusCode() + ": " + response.body());
        }
        return objectMapper.readValue(response.body(), responseType);
    }

    private URI uri(String path) {
        return URI.create(baseUrl + path);
    }

    private String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }
}
