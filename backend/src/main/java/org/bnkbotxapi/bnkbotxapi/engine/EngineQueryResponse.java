package org.bnkbotxapi.bnkbotxapi.engine;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class EngineQueryResponse {

    private String answer;

    private boolean handoff;

    private List<EngineSourceDTO> sources = new ArrayList<>();

    private List<EngineSourceDTO> related = new ArrayList<>();
}
