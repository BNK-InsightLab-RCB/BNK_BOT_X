package org.bnkbotxapi.bnkbotxapi.chat.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ChatQueryRequestDTO {

    @NotBlank
    private String question;

    private Integer topK = 5;

    private String mode = "branch";
}
