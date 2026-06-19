package org.bnkbotxapi.bnkbotxapi.engine;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class EngineManualListResponse {

    private List<EngineManualSummaryDTO> items = new ArrayList<>();
}
