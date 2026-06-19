package org.bnkbotxapi.bnkbotxapi.chat.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.log4j.Log4j2;
import org.bnkbotxapi.bnkbotxapi.account.domain.AccountRole;
import org.bnkbotxapi.bnkbotxapi.chat.domain.ChatLogEntity;
import org.bnkbotxapi.bnkbotxapi.chat.dto.*;
import org.bnkbotxapi.bnkbotxapi.chat.repository.ChatLogRepository;
import org.bnkbotxapi.bnkbotxapi.engine.ChatbotEngineClient;
import org.bnkbotxapi.bnkbotxapi.engine.EngineQueryResponse;
import org.bnkbotxapi.bnkbotxapi.engine.EngineSourceDTO;
import org.bnkbotxapi.bnkbotxapi.security.auth.CustomUserPrincipal;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Log4j2
@Transactional
@RequiredArgsConstructor
public class ChatService {

    private final ChatbotEngineClient engineClient;
    private final ChatLogRepository chatLogRepository;

    public ChatQueryResponseDTO query(ChatQueryRequestDTO request, CustomUserPrincipal principal) {
        String engineRole = resolveEngineRole(request.getMode(), principal);
        int topK = request.getTopK() == null ? 5 : request.getTopK();

        EngineQueryResponse engineResponse = engineClient.query(request.getQuestion(), engineRole, topK);

        ChatLogEntity saved = chatLogRepository.save(ChatLogEntity.builder()
                .accountId(principal.getAccountId())
                .loginId(principal.getUsername())
                .accountRole(principal.getRole().name())
                .question(request.getQuestion())
                .answer(engineResponse.getAnswer())
                .handoff(engineResponse.isHandoff())
                .build());

        return ChatQueryResponseDTO.builder()
                .chatLogId(saved.getChatLogId())
                .answer(engineResponse.getAnswer())
                .handoff(engineResponse.isHandoff())
                .sources(toSources(engineResponse.getSources()))
                .related(toSources(engineResponse.getRelated()))
                .regDate(saved.getRegDate())
                .build();
    }

    @Transactional(readOnly = true)
    public List<ChatHistoryDTO> history(CustomUserPrincipal principal) {
        return chatLogRepository.findTop30ByAccountIdOrderByChatLogIdDesc(principal.getAccountId())
                .stream()
                .map(log -> ChatHistoryDTO.builder()
                        .chatLogId(log.getChatLogId())
                        .question(log.getQuestion())
                        .answer(log.getAnswer())
                        .handoff(log.isHandoff())
                        .regDate(log.getRegDate())
                        .build())
                .toList();
    }

    private String resolveEngineRole(String requestedMode, CustomUserPrincipal principal) {
        if (principal.getRole() == AccountRole.ADMIN && "it".equalsIgnoreCase(requestedMode)) {
            return "it";
        }
        return "branch";
    }

    private List<SourceDTO> toSources(List<EngineSourceDTO> sources) {
        if (sources == null) {
            return List.of();
        }
        return sources.stream()
                .map(source -> SourceDTO.builder()
                        .manualId(source.getManualId())
                        .screenKo(source.getScreenKo())
                        .action(source.getAction())
                        .score(source.getScore())
                        .build())
                .toList();
    }
}
