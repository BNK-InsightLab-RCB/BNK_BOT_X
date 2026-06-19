package org.bnkbotxapi.bnkbotxapi.config;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1")
public class HealthCheckController {

    @GetMapping("health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "service", "bnk-bot-x-api");
    }
}
