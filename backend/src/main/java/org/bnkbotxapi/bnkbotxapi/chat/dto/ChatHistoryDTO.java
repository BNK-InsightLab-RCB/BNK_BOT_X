package org.bnkbotxapi.bnkbotxapi.chat.dto;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class ChatHistoryDTO {

    private Long chatLogId;

    private String question;

    private String answer;

    private boolean handoff;

    private LocalDateTime regDate;
}
