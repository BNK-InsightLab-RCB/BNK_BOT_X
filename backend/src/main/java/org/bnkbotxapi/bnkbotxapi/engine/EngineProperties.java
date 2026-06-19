package org.bnkbotxapi.bnkbotxapi.engine;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "bnk.engine")
public class EngineProperties {

    private String baseUrl = "http://localhost:9000";
}
