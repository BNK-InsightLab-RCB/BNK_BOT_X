package org.bnkbotxapi.bnkbotxapi.account.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.bnkbotxapi.bnkbotxapi.account.dto.AccountReadDTO;
import org.bnkbotxapi.bnkbotxapi.account.dto.LoginRequestDTO;
import org.bnkbotxapi.bnkbotxapi.account.dto.LoginResponseDTO;
import org.bnkbotxapi.bnkbotxapi.account.service.AuthService;
import org.bnkbotxapi.bnkbotxapi.security.auth.CustomUserPrincipal;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("login")
    public ResponseEntity<LoginResponseDTO> login(@Valid @RequestBody LoginRequestDTO request) {
        return ResponseEntity.ok(authService.login(request));
    }

    @PostMapping("refresh")
    public ResponseEntity<LoginResponseDTO> refresh(@RequestBody Map<String, String> body) {
        return ResponseEntity.ok(authService.refresh(body.get("refreshToken")));
    }

    @PostMapping("logout")
    public ResponseEntity<String> logout(@AuthenticationPrincipal CustomUserPrincipal principal) {
        authService.logout(principal);
        return ResponseEntity.ok("Successfully logout");
    }

    @GetMapping("me")
    public ResponseEntity<AccountReadDTO> me(@AuthenticationPrincipal CustomUserPrincipal principal) {
        return ResponseEntity.ok(authService.me(principal));
    }
}
