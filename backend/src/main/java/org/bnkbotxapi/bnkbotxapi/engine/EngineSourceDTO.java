package org.bnkbotxapi.bnkbotxapi.engine;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class EngineSourceDTO {

    @JsonProperty("manual_id")
    private String manualId;

    @JsonProperty("screen_ko")
    private String screenKo;

    private String action;

    private Double score;
}
