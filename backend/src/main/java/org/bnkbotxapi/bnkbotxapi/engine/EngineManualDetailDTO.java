package org.bnkbotxapi.bnkbotxapi.engine;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Data
public class EngineManualDetailDTO {

    private String id;

    @JsonProperty("screen_id")
    private String screenId;

    @JsonProperty("screen_ko")
    private String screenKo;

    private String action;

    @JsonProperty("api_path")
    private String apiPath;

    @JsonProperty("table_en")
    private List<String> tableEn = new ArrayList<>();

    @JsonProperty("table_ko")
    private List<String> tableKo = new ArrayList<>();

    @JsonProperty("branch_md")
    private String branchMd;

    @JsonProperty("it_md")
    private String itMd;

    private Map<String, Object> facts;

    @JsonProperty("lineage_ref")
    private List<String> lineageRef = new ArrayList<>();

    private String status;

    private Integer version;

    @JsonProperty("reviewed_at")
    private String reviewedAt;

    @JsonProperty("reviewed_by")
    private String reviewedBy;
}
