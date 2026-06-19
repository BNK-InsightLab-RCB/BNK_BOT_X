package org.bnkbotxapi.bnkbotxapi.chat.dto;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
public class ChatQueryResponseDTO {

    private Long chatLogId;

    private String answer;

    private boolean handoff;

    private List<SourceDTO> sources;

    private List<SourceDTO> related;

    private LocalDateTime regDate;
}
