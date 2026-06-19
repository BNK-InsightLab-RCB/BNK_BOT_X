package org.bnkbotxapi.bnkbotxapi.engine;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class EngineManualSummaryDTO {

    private String id;

    private String status;

    private Integer version;

    private String action;

    @JsonProperty("reviewed_at")
    private String reviewedAt;

    @JsonProperty("screen_ko")
    private String screenKo;
}
