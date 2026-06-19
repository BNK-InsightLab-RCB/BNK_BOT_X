package org.bnkbotxapi.bnkbotxapi.chat.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class SourceDTO {

    private String manualId;

    private String screenKo;

    private String action;

    private Double score;
}
