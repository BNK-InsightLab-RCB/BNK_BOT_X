package org.bnkbotxapi.bnkbotxapi.account.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class LoginRequestDTO {

    @NotBlank
    private String loginId;

    @NotBlank
    private String password;
}
