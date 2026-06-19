package org.bnkbotxapi.bnkbotxapi.engine;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class EngineManualEditRequest {

    @JsonProperty("branch_md")
    private String branchMd;

    @JsonProperty("it_md")
    private String itMd;

    private String by;
}
