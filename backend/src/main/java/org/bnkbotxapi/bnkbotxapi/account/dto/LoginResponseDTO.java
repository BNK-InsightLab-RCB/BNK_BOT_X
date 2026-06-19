package org.bnkbotxapi.bnkbotxapi.account.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class LoginResponseDTO {

    private String accessToken;

    private String refreshToken;

    private Long accountId;

    private String loginId;

    private String name;

    private String role;
}
