package org.bnkbotxapi.bnkbotxapi.chat.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.bnkbotxapi.bnkbotxapi.chat.dto.ChatHistoryDTO;
import org.bnkbotxapi.bnkbotxapi.chat.dto.ChatQueryRequestDTO;
import org.bnkbotxapi.bnkbotxapi.chat.dto.ChatQueryResponseDTO;
import org.bnkbotxapi.bnkbotxapi.chat.service.ChatService;
import org.bnkbotxapi.bnkbotxapi.security.auth.CustomUserPrincipal;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/chat")
@RequiredArgsConstructor
public class ChatController {

    private final ChatService chatService;

    @PostMapping("query")
    public ResponseEntity<ChatQueryResponseDTO> query(
            @Valid @RequestBody ChatQueryRequestDTO request,
            @AuthenticationPrincipal CustomUserPrincipal principal) {

        return ResponseEntity.ok(chatService.query(request, principal));
    }

    @GetMapping("history")
    public ResponseEntity<List<ChatHistoryDTO>> history(@AuthenticationPrincipal CustomUserPrincipal principal) {
        return ResponseEntity.ok(chatService.history(principal));
    }
}
