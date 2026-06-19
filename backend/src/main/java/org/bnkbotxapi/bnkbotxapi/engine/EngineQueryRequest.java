package org.bnkbotxapi.bnkbotxapi.engine;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class EngineQueryRequest {

    private String question;

    private String role;

    @JsonProperty("top_k")
    private int topK;
}
