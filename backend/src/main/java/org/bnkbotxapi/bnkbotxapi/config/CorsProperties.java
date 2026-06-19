package org.bnkbotxapi.bnkbotxapi.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "bnk.cors")
public class CorsProperties {

    private String allowedOrigins = "http://localhost:5173";
}
